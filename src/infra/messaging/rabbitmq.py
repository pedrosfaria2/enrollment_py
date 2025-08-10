from __future__ import annotations

import json
import threading
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPError

from settings import cfg


class RabbitPublisher:
    """RabbitMQ message publisher for enrollment events.
    """
    
    def __init__(self, url: str | None = None, queue: str = cfg.QUEUE_NAME) -> None:
        """Initialize RabbitMQ publisher.
        
        Args:
            url: RabbitMQ connection URL (default: from config)
            queue: Queue name to publish to (default: from config)
        """
        self._url = url or cfg.RABBITMQ_URL
        self._queue = queue
        self._conn: pika.BlockingConnection | None = None
        self._ch: BlockingChannel | None = None
        self._lock = threading.Lock()
        self._unroutable = False

    def _on_return(self, _ch, _method, _properties, _body) -> None:
        """Callback for unroutable messages.
        
        Args:
            _ch: Channel that returned the message
            _method: Method frame
            _properties: Message properties
            _body: Message body
        """
        self._unroutable = True

    def _ensure_channel(self) -> BlockingChannel:
        """Ensure RabbitMQ channel is open and configured.
        
        Creates new connection and channel if needed, declares queue,
        and sets up delivery confirmation.
        
        Returns:
            Active RabbitMQ channel
        """
        if self._conn and self._conn.is_open and self._ch and self._ch.is_open:
            return self._ch
        params = pika.URLParameters(self._url)
        conn = pika.BlockingConnection(params)
        ch: BlockingChannel = conn.channel()
        ch.queue_declare(queue=self._queue, durable=True, auto_delete=False)
        ch.confirm_delivery()
        ch.add_on_return_callback(self._on_return)
        self._conn = conn
        self._ch = ch
        return ch

    def _reset(self) -> None:
        """Reset connection and channel state.
        
        Closes existing connection and resets internal state.
        """
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        self._conn = None
        self._ch = None

    def publish(self, payload: dict[str, Any]) -> None:
        """Publish message to RabbitMQ queue.
        
        Serializes payload to JSON and publishes with delivery confirmation.
        Thread-safe operation with automatic connection management.
        
        Args:
            payload: Message data to publish
            
        Raises:
            RuntimeError: If message publishing fails or is unroutable
        """
        body = json.dumps(payload).encode("utf-8")
        props = pika.BasicProperties(content_type="application/json", delivery_mode=2)
        with self._lock:
            try:
                self._unroutable = False
                ch = self._ensure_channel()
                ch.basic_publish(
                    exchange="",
                    routing_key=self._queue,
                    body=body,
                    properties=props,
                    mandatory=True,
                )
                if self._unroutable:
                    raise AMQPError("message was returned (unroutable)")
            except Exception as e:
                self._reset()
                raise RuntimeError(f"publish failed: {e}") from e

    def close(self) -> None:
        """Close RabbitMQ connection and cleanup resources.
        
        Thread-safe operation that closes connection and resets state.
        """
        with self._lock:
            self._reset()
