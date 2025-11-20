from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


class WebSocketMetrics:
    """Prometheus metrics helpers for WebSocket broadcasting."""

    def __init__(self) -> None:
        self._messages_sent = Counter(
            "websocket_messages_sent_total",
            "Number of WebSocket messages successfully delivered.",
            labelnames=("manager",),
        )
        self._messages_failed = Counter(
            "websocket_messages_failed_total",
            "Number of WebSocket messages that failed to deliver.",
            labelnames=("manager",),
        )
        self._broadcast_duration = Histogram(
            "websocket_broadcast_duration_seconds",
            "Time spent broadcasting WebSocket messages.",
            labelnames=("manager",),
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )
        self._active_connections = Gauge(
            "websocket_active_connections",
            "Active WebSocket connections managed by this process.",
            labelnames=("manager",),
        )

    def observe_broadcast(self, manager: str, sent: int, failed: int, duration: float) -> None:
        """Record broadcast duration and success/failure counters."""
        self._broadcast_duration.labels(manager=manager).observe(duration)
        if sent:
            self._messages_sent.labels(manager=manager).inc(sent)
        if failed:
            self._messages_failed.labels(manager=manager).inc(failed)

    def inc_active(self, manager: str) -> None:
        self._active_connections.labels(manager=manager).inc()

    def dec_active(self, manager: str) -> None:
        self._active_connections.labels(manager=manager).dec()


websocket_metrics = WebSocketMetrics()
