from asyncio import Queue
from typing import Optional
from app.gateway.dto import ProgressEvent, EventStatus


class ProgressEmitter:
    def __init__(self, queue: Queue):
        self.queue = queue

    async def emit(self, status: EventStatus, data: Optional[dict] = None):
        message = ProgressEvent(status=status, data=data)
        await self.queue.put(message)

    async def close(self):
        # Sentinel value to indicate completion
        await self.queue.put(None)
