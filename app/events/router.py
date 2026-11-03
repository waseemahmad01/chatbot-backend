import json 

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.auth.dependencies import get_current_user
from app.events.eventBus import event_bus

router = APIRouter(prefix="", tags=["events"])


@router.get("/stream/{request_id}")
async def stream_events(request: Request, request_id:int):
    queue = event_bus.subscribe(request_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                event = await queue.get()
                if event is None:
                    break

                yield (
                    f"event: {event['type']}\n"
                    f"data: {json.dumps(event['data'])}\n\n"
                )
        finally:
            event_bus.unsubscribe(request_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")