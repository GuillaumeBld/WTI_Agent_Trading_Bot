"""Async scheduling primitives for orchestrating the trading agents."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)

Payload = Dict[str, Any]
Consumer = Callable[[Payload], Awaitable[None]]


@dataclass
class DataChannel:
    """Typed channel that transports payloads between producers and consumers."""

    name: str
    queue: asyncio.Queue[Payload] = field(default_factory=lambda: asyncio.Queue(maxsize=100))

    async def publish(self, payload: Payload) -> None:
        logger.debug("Publishing payload to channel %s", self.name)
        await self.queue.put(payload)

    async def subscribe(self) -> Payload:
        payload = await self.queue.get()
        self.queue.task_done()
        return payload


class Scheduler:
    """Simple asynchronous scheduler with per-channel instrumentation."""

    def __init__(self) -> None:
        self.channels: Dict[str, DataChannel] = {}
        self.consumers: Dict[str, list[Consumer]] = defaultdict(list)
        self._tasks: list[asyncio.Task[Any]] = []

    def get_channel(self, name: str) -> DataChannel:
        if name not in self.channels:
            self.channels[name] = DataChannel(name=name)
        return self.channels[name]

    def register_consumer(self, channel: str, consumer: Consumer) -> None:
        self.consumers[channel].append(consumer)

    async def start(self) -> None:
        logger.info("Scheduler starting with channels: %s", list(self.channels))
        for channel_name, consumers in self.consumers.items():
            channel = self.get_channel(channel_name)
            self._tasks.append(asyncio.create_task(self._dispatch_loop(channel, consumers)))

    async def _dispatch_loop(self, channel: DataChannel, consumers: list[Consumer]) -> None:
        while True:
            payload = await channel.subscribe()
            for consumer in consumers:
                try:
                    await consumer(payload)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Consumer error on channel %s: %s", channel.name, exc)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()


__all__ = ["Scheduler", "DataChannel"]
