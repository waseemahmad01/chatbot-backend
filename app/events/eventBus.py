import asyncio
import time
from collections import defaultdict


class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(asyncio.Queue)
    
    def subscribe(self, request_id:int):
        return self.subscribers[request_id]

    async def publish(self, request_id:int ,event_type:str, data):
        queue = self.subscribers.get(request_id)
        start = time.perf_counter()
        print(f"Publishing event {event_type} to {request_id}")
        if queue:
               await queue.put({
                "type": event_type,
                "data": data
            })
        print(f"Publish took {(time.perf_counter() - start) * 1000:.2f} ms")
    async def close(self, request_id: int):
        queue = self.subscribers.get(request_id)
        if queue:
            await queue.put(None)

    def unsubscribe(self, request_id: int):
        self.subscribers.pop(request_id, None)

event_bus = EventBus()
