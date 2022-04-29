from ._websocket_stream import _USDCWebSocketManager
from ._websocket_stream import USDC_PERPETUAL
from ._websocket_stream import _identify_ws_method, _make_public_kwargs


ws_name = USDC_PERPETUAL
PUBLIC_WSS = "wss://{SUBDOMAIN}.{DOMAIN}.com/perpetual/ws/v1/realtime_public"
PRIVATE_WSS = "wss://{SUBDOMAIN}.{DOMAIN}.com/trade/option/usdc/private/v1"


class WebSocket(_USDCWebSocketManager):
    def __init__(self, **kwargs):
        super().__init__(ws_name, **kwargs)

        self.ws_public = None
        self.ws_private = None

        self.kwargs = kwargs
        self.public_kwargs = _make_public_kwargs(self.kwargs)

    def _ws_public_subscribe(self, topic, callback, symbol):
        if not self.ws_public:
            self.ws_public = _USDCWebSocketManager(
                ws_name, **self.public_kwargs)
            self.ws_public._connect(PUBLIC_WSS)
        self.ws_public.subscribe(topic, callback, symbol)

    def _ws_private_subscribe(self, topic, callback):
        if not self.ws_private:
            self.ws_private = _USDCWebSocketManager(
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
        symbol = _USDCWebSocketManager._extract_symbol(topic)
        if symbol:
            subscribe(topic, callback, symbol)
        else:
            subscribe(topic, callback)

    def orderbook_25_stream(self, callback, symbol):
        """
        This topic always returns messages in the "snapshot" format for a
        simplified user experience. pybit processes the delta/snapshot
        messages for you. Read the Bybit API documentation for more information.

        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorderbook
        """
        topic = "orderBookL2_25.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def orderbook_200_stream(self, callback, symbol):
        """
        This topic always returns messages in the "snapshot" format for a
        simplified user experience. pybit processes the delta/snapshot
        messages for you. Read the Bybit API documentation for more information.

        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorderbook
        """
        topic = "orderBook_200.100ms.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def trade_stream(self, callback, symbol):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websockettrade
        """
        topic = "trade.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def instrument_info_stream(self, callback, symbol):
        """
        This topic always returns messages in the "snapshot" format for a
        simplified user experience. pybit processes the delta/snapshot
        messages for you. Read the Bybit API documentation for more information.

        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketinstrumentinfo
        """
        topic = "instrument_info.100ms.{}"
        self._ws_public_subscribe(topic, callback, symbol)

    def kline_stream(self, callback, symbol, interval):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketkline
        """
        topic = "candle.{}.{}"
        topic = topic.format(str(interval), "{}")
        self._ws_public_subscribe(topic, callback, symbol)

    def position_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketposition
        """
        topic = "user.openapi.perp.position"
        self._ws_private_subscribe(topic=topic, callback=callback)

    def execution_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketexecution
        """
        topic = "user.openapi.perp.trade"
        self._ws_private_subscribe(topic=topic, callback=callback)

    def order_stream(self, callback):
        """
        https://bybit-exchange.github.io/docs/usdc/perpetual/#t-websocketorder
        """
        topic = "user.openapi.perp.order"
        self._ws_private_subscribe(topic=topic, callback=callback)
