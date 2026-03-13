import asyncio

class EventBus:

    def __init__(self):
        self.subscribers = []

    async def publish(self, event):
        for queue in self.subscribers:
            await queue.put(event)

    def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue


event_bus = EventBus()
