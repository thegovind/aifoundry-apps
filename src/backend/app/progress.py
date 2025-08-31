import asyncio
import json
from typing import Dict, Optional, AsyncIterator


class ProgressBroker:
    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue] = {}
        self._cancelled: set[str] = set()

    def get_queue(self, job_id: str) -> asyncio.Queue:
        if job_id not in self._queues:
            self._queues[job_id] = asyncio.Queue()
        return self._queues[job_id]

    async def publish(self, job_id: str, event: str, data: Optional[dict] = None) -> None:
        queue = self.get_queue(job_id)
        payload = {"event": event, "data": data or {}}
        await queue.put(payload)

    async def stream(self, job_id: str, keepalive: float = 15.0) -> AsyncIterator[bytes]:
        queue = self.get_queue(job_id)
        last_sent = asyncio.get_event_loop().time()
        while True:
            if job_id in self._cancelled:
                yield b"event: done\ndata: {\"status\":\"cancelled\"}\n\n"
                break
            try:
                item = await asyncio.wait_for(queue.get(), timeout=keepalive)
                msg = f"event: {item['event']}\n" + f"data: {json.dumps(item['data'])}\n\n"
                yield msg.encode("utf-8")
                last_sent = asyncio.get_event_loop().time()
                if item.get("event") == "done":
                    break
            except asyncio.TimeoutError:
                # Send comment as keepalive
                yield b": keep-alive\n\n"
                # loop continues

    def cancel(self, job_id: str) -> None:
        self._cancelled.add(job_id)

    def is_cancelled(self, job_id: str) -> bool:
        return job_id in self._cancelled


# Singleton broker instance
broker = ProgressBroker()
