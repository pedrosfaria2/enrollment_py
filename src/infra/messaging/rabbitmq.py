from __future__ import annotations

import json
import threading
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPError

from settings import cfg


class RabbitPublisher:
    def __init__(self, url: str | None = None, queue: str = cfg.QUEUE_NAME) -> None:
        self._url = url or cfg.RABBITMQ_URL
        self._queue = queue
        self._conn: pika.BlockingConnection | None = None
        self._ch: BlockingChannel | None = None
        self._lock = threading.Lock()

    def _ensure_channel(self) -> BlockingChannel:
        if self._conn and self._conn.is_open and self._ch and self._ch.is_open:
            return self._ch
        params = pika.URLParameters(self._url)
        conn = pika.BlockingConnection(params)
        ch: BlockingChannel = conn.channel()
        ch.queue_declare(queue=self._queue, durable=True, auto_delete=False)
        ch.confirm_delivery()
        self._conn = conn
        self._ch = ch
        return ch

    def _reset(self) -> None:
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        self._conn = None
        self._ch = None

    def publish(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        props = pika.BasicProperties(content_type="application/json", delivery_mode=2)
        with self._lock:
            try:
                ch = self._ensure_channel()
                ok = ch.basic_publish(
                    exchange="",
                    routing_key=self._queue,
                    body=body,
                    properties=props,
                    mandatory=True,
                )
                if not ok:
                    raise AMQPError("broker did not confirm publish")
            except Exception as e:
                self._reset()
                raise RuntimeError(f"publish failed: {e}") from e

    def close(self) -> None:
        with self._lock:
            self._reset()
