from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ...progress import broker

router = APIRouter()

@router.get("/progress/{job_id}/stream")
async def progress_stream(job_id: str):
    async def event_generator():
        async for chunk in broker.stream(job_id):
            yield chunk
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/progress/{job_id}/cancel")
async def progress_cancel(job_id: str):
    broker.cancel(job_id)
    return {"status": "cancelled", "job_id": job_id}
