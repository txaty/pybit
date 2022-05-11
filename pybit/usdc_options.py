from ._websocket_stream import _USDCOptionsWebSocketManager
from ._websocket_stream import USDC_OPTIONS
from ._websocket_stream import _identify_ws_method, _make_public_kwargs


ws_name = USDC_OPTIONS
PUBLIC_WSS = "wss://{SUBDOMAIN}.{DOMAIN}.com/trade/option/usdc/public/v1"
PRIVATE_WSS = "wss://{SUBDOMAIN}.{DOMAIN}.com/trade/option/usdc/private/v1"


class WebSocket(_USDCOptionsWebSocketManager):
    def __init__(self, **kwargs):
        super().__init__(ws_name, **kwargs)

        self.ws_public = None
        self.ws_private = None

        self.kwargs = kwargs
        self.public_kwargs = _make_public_kwargs(self.kwargs)

    def _ws_public_subscribe(self, topic, callback, symbol=None):
        if not self.ws_public:
            self.ws_public = _USDCOptionsWebSocketManager(
                ws_name, **self.public_kwargs)
            self.ws_public._connect(PUBLIC_WSS)
        self.ws_public.subscribe(topic, callback, symbol)

    def _ws_private_subscribe(self, topic, callback):
        if not self.ws_private:
            self.ws_private = _USDCOptionsWebSocketManager(
                ws_name, **self.kwargs)
            self.ws_private._connect(PRIVATE_WSS)
        self.ws_private.subscribe(topic, callback)

    def custom_topic_stream(self, wss_url, topic, callback):
        subscribe = _identify_ws_method(
            wss_url,
            {
                PUBLIC_WSS: self._ws_public_subscribe,
                PRIVATE_WSS: self._ws_private_subscribe
            })
        symbol = self._extract_symbol(topic)
        if symbol:
            subscribe(topic, callback, symbol)
        else:
            subscribe(topic, callback)

    def orderbook_25_stream(self, callback, symbol):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorderbook
        """
        topic = "orderbook25.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def orderbook_100_stream(self, callback, symbol):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorderbook
        """
        topic = "orderbook100.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def delta_orderbook_100_stream(self, callback, symbol):
        """
        This topic always returns messages in the "snapshot" format for a
        simplified user experience. pybit processes the delta/snapshot
        messages for you. Read the Bybit API documentation for more information.

        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorderbook
        """
        topic = "delta.orderbook100.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def trade_stream(self, callback, symbol):
        """
        symbol should be the currency. Eg, "BTC" instead of
        "BTC-13MAY22-25000-C"
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websockettrade
        """
        topic = "recenttrades.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def instrument_info_stream(self, callback, symbol):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketinstrumentinfo
        """
        topic = "instrument_info.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def insurance_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/inverse/#t-websocketinsurance
        """
        topic = "platform.insurance.USDC"
        self._ws_public_subscribe(topic, callback)

    def position_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketposition
        """
        topic = "user.openapi.option.position"
        self._ws_private_subscribe(topic=topic, callback=callback)

    def execution_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketexecution
        """
        topic = "user.openapi.option.trade"
        self._ws_private_subscribe(topic=topic, callback=callback)

    def order_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorder
        """
        topic = "user.openapi.option.order"
        self._ws_private_subscribe(topic=topic, callback=callback)
