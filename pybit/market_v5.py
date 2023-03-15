"""
Market HTTP V5 APIs
"""
from pybit.pybit._http_v5_manager import _V5HTTPManager


class HTTP(_V5HTTPManager):
    def query_kline(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/kline",
            query=kwargs,
            auth=True,
        )

    def query_mark_price_kline(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/mark-price-kline",
            query=kwargs,
            auth=True,
        )

    def query_index_price_kline(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/index-price-kline",
            query=kwargs,
            auth=True,
        )

    def query_premium_index_price_kline(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/premium-index-price-kline",
            query=kwargs,
            auth=True,
        )

    def query_instrument_info(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/instruments-info",
            query=kwargs,
            auth=True,
        )

    def query_orderbook(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/orderbook",
            query=kwargs,
            auth=True,
        )

    def query_tickers(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/tickers",
            query=kwargs,
            auth=True,
        )

    def query_funding_rate_history(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/funding/history",
            query=kwargs,
            auth=True,
        )

    def query_public_trading_history(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/recent-trade",
            query=kwargs,
            auth=True,
        )

    def query_open_interest(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/open-interest",
            query=kwargs,
            auth=True,
        )

    def query_historical_volatility(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/historical-volatility",
            query=kwargs,
            auth=True,
        )

    def query_risk_limit(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/risk-limit",
            query=kwargs,
            auth=True,
        )

    def query_option_delivery_price(self, **kwargs):
        return self._submit_request(
            method="GET",
            path=self.endpoint + "/v5/market/delivery-price",
            query=kwargs,
            auth=True,
        )
