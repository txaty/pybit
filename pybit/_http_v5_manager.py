"""
HTTP V5 endpoints.
"""
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime as dt
from json import JSONDecodeError

import requests

from . import _helpers, InvalidRequestError, FailedRequestError

VERSION = "3.0.0rc5"


class _V5HTTPManager:
    def __init__(
        self,
        endpoint=None,
        api_key=None,
        api_secret=None,
        logging_level=logging.INFO,
        log_requests=False,
        request_timeout=10,
        recv_window=5000,
        force_retry=False,
        retry_codes=None,
        ignore_codes=None,
        max_retries=3,
        retry_delay=3,
        referral_id=None,
        record_request_time=False,
    ):
        """Initializes the HTTP class."""

        # Set the endpoint.
        if endpoint is None:
            self.endpoint = "https://api.bybit.com"
        else:
            self.endpoint = endpoint

        # Setup logger.

        self.logger = logging.getLogger(__name__)

        if len(logging.root.handlers) == 0:
            # no handler on root logger set -> we add handler just for this logger to not mess with custom logic from outside
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            handler.setLevel(logging_level)
            self.logger.addHandler(handler)

        self.logger.debug("Initializing HTTP session.")
        self.log_requests = log_requests

        # Set API keys.
        self.api_key = api_key
        self.api_secret = api_secret

        # Set timeout.
        self.timeout = request_timeout
        self.recv_window = recv_window
        self.force_retry = force_retry
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Set whitelist of non-fatal Bybit status codes to retry on.
        if retry_codes is None:
            self.retry_codes = {10002, 10006, 30034, 30035, 130035, 130150}
        else:
            self.retry_codes = retry_codes

        # Set whitelist of non-fatal Bybit status codes to ignore.
        if ignore_codes is None:
            self.ignore_codes = set()
        else:
            self.ignore_codes = ignore_codes

        # Initialize requests session.
        self.client = requests.Session()
        self.client.headers.update(
            {
                "User-Agent": "pybit-" + VERSION,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Add referral ID to header.
        self.referral_id = referral_id
        if referral_id:
            self.client.headers.update({"Referer": referral_id})

        # If true, records and returns the request's elapsed time in a tuple
        # with the response body.
        self.record_request_time = record_request_time

    @staticmethod
    def prepare_payload(method, parameters):
        """
        Prepares the request payload and validates parameter value types.
        """

        def cast_values():
            string_params = ["qty", "price", "triggerPrice", "takeProfit", "stopLoss"]
            integer_params = ["positionIdx"]
            for key, value in parameters.items():
                if key in string_params:
                    if type(value) != str:
                        parameters[key] = str(value)
                elif key in integer_params:
                    if type(value) != int:
                        parameters[key] = int(value)

        if method == "GET":
            payload = "&".join(
                [
                    str(k) + "=" + str(v)
                    for k, v in sorted(parameters.items())
                    if v is not None
                ]
            )
            return payload
        else:
            cast_values()
            return json.dumps(parameters)

    def _auth(self, payload, recv_window, timestamp):
        """
        Generates authentication signature per Bybit API specifications.
        """

        api_key = self.api_key
        api_secret = self.api_secret

        if api_key is None or api_secret is None:
            raise PermissionError("Authenticated endpoints require keys.")

        param_str = str(timestamp) + api_key + str(recv_window) + payload
        hash = hmac.new(
            bytes(api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256
        )
        return hash.hexdigest()

    @staticmethod
    def _verify_string(params, key):
        if key in params:
            if not isinstance(params[key], str):
                return False
            else:
                return True
        return True

    def _submit_request(self, method=None, path=None, query=None, auth=False):
        """
        Submits the request to the API.

        Notes
        -------------------
        We use the params argument for the GET method, and data argument for
        the POST method. Dicts passed to the data argument must be
        JSONified prior to submitting request.

        """

        if query is None:
            query = {}

        # Remove internal spot arg
        query.pop("spot", "")

        # Store original recv_window.
        recv_window = self.recv_window

        # Bug fix: change floating whole numbers to integers to prevent
        # auth signature errors.
        if query is not None:
            for i in query.keys():
                if isinstance(query[i], float) and query[i] == int(query[i]):
                    query[i] = int(query[i])

        # Send request and return headers with body. Retry if failed.
        retries_attempted = self.max_retries
        req_params = None

        while True:

            retries_attempted -= 1
            if retries_attempted < 0:
                raise FailedRequestError(
                    request=f"{method} {path}: {req_params}",
                    message="Bad Request. Retries exceeded maximum.",
                    status_code=400,
                    time=dt.utcnow().strftime("%H:%M:%S"),
                )

            retries_remaining = f"{retries_attempted} retries remain."

            req_params = self.prepare_payload(method, query)

            # Authenticate if we are using a private endpoint.
            if auth:
                # Prepare signature.
                timestamp = _helpers.generate_timestamp()
                signature = self._auth(
                    payload=req_params,
                    recv_window=recv_window,
                    timestamp=timestamp,
                )
                headers = {
                    "Content-Type": "application/json",
                    "X-BAPI-API-KEY": self.api_key,
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-SIGN-TYPE": "2",
                    "X-BAPI-TIMESTAMP": str(timestamp),
                    "X-BAPI-RECV-WINDOW": str(recv_window),
                }
            else:
                headers = {}

            # Log the request.
            if self.log_requests:
                if req_params:
                    self.logger.debug(
                        f"Request -> {method} {path}. Body: {req_params}. "
                        f"Headers: {headers}"
                    )
                else:
                    self.logger.debug(f"Request -> {method} {path}. Headers: {headers}")

            if method == "GET":
                if req_params:
                    r = self.client.prepare_request(
                        requests.Request(
                            method, path + f"?{req_params}", headers=headers
                        )
                    )
                else:
                    r = self.client.prepare_request(
                        requests.Request(method, path, headers=headers)
                    )
            else:
                r = self.client.prepare_request(
                    requests.Request(method, path, data=req_params, headers=headers)
                )

            # Attempt the request.
            try:
                s = self.client.send(r, timeout=self.timeout)

            # If requests fires an error, retry.
            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
            ) as e:
                if self.force_retry:
                    self.logger.error(f"{e}. {retries_remaining}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise e

            # Check HTTP status code before trying to decode JSON.
            if s.status_code != 200:
                if s.status_code == 403:
                    error_msg = "You have breached the IP rate limit."
                else:
                    error_msg = "HTTP status code is not 200."
                self.logger.debug(f"Response text: {s.text}")
                raise FailedRequestError(
                    request=f"{method} {path}: {req_params}",
                    message=error_msg,
                    status_code=s.status_code,
                    time=dt.utcnow().strftime("%H:%M:%S"),
                )

            # Convert response to dictionary, or raise if requests error.
            try:
                s_json = s.json()

            # If we have trouble converting, handle the error and retry.
            except JSONDecodeError as e:
                if self.force_retry:
                    self.logger.error(f"{e}. {retries_remaining}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    self.logger.debug(f"Response text: {s.text}")
                    raise FailedRequestError(
                        request=f"{method} {path}: {req_params}",
                        message="Conflict. Could not decode JSON.",
                        status_code=409,
                        time=dt.utcnow().strftime("%H:%M:%S"),
                    )

            ret_code = "retCode"
            ret_msg = "retMsg"

            # If Bybit returns an error, raise.
            if s_json[ret_code]:

                # Generate error message.
                error_msg = f"{s_json[ret_msg]} (ErrCode: {s_json[ret_code]})"

                # Set default retry delay.
                err_delay = self.retry_delay

                # Retry non-fatal whitelisted error requests.
                if s_json[ret_code] in self.retry_codes:

                    # 10002, recv_window error; add 2.5 seconds and retry.
                    if s_json[ret_code] == 10002:
                        error_msg += ". Added 2.5 seconds to recv_window"
                        recv_window += 2500

                    # 10006, ratelimit error; wait until rate_limit_reset_ms
                    # and retry.
                    elif s_json[ret_code] == 10006:
                        self.logger.error(
                            f"{error_msg}. Ratelimited on current request. "
                            f"Sleeping, then trying again. Request: {path}"
                        )

                        # Calculate how long we need to wait.
                        limit_reset = s_json["rate_limit_reset_ms"] / 1000
                        reset_str = time.strftime("%X", time.localtime(limit_reset))
                        err_delay = int(limit_reset) - int(time.time())
                        error_msg = (
                            f"Ratelimit will reset at {reset_str}. "
                            f"Sleeping for {err_delay} seconds"
                        )

                    # Log the error.
                    self.logger.error(f"{error_msg}. {retries_remaining}")
                    time.sleep(err_delay)
                    continue

                elif s_json[ret_code] in self.ignore_codes:
                    pass

                else:
                    raise InvalidRequestError(
                        request=f"{method} {path}: {req_params}",
                        message=s_json[ret_msg],
                        status_code=s_json[ret_code],
                        time=dt.utcnow().strftime("%H:%M:%S"),
                    )
            else:
                if self.record_request_time:
                    return s_json, s.elapsed
                else:
                    return s_json

    def get_server_time(self):
        return self._submit_request(
            method="GET", path=self.endpoint + "/v5/public/time", auth=False
        )

    def get_api_key_info(self):
        return self._submit_request(
            method="GET", path=self.endpoint + "/user/v5/private/query-api", auth=True
        )
