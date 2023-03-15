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
