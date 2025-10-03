import os

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import conint

router = APIRouter(prefix="/other", tags=["Other"])

MAX_TEST_FILE_SIZE = 64 * 1024  # 64 KiB


def random_bytes(size: int):
    # yields random bytes in 1KiB chunks until size is reached
    chunk_size = 1024
    remaining = size
    while remaining > 0:
        to_read = min(chunk_size, remaining)
        yield os.urandom(to_read)
        remaining -= to_read


@router.post("/upload-test")
async def upload_test(request: Request):
    uploaded_len = 0
    async for chunk in request.stream():
        uploaded_len += len(chunk)
        if uploaded_len > MAX_TEST_FILE_SIZE:
            raise HTTPException(413, "Request file too big")
    return Response(status_code=200)


@router.get("/download-test")
def download_test(file_size: conint(ge=1, le=MAX_TEST_FILE_SIZE)):
    if file_size > MAX_TEST_FILE_SIZE:
        raise HTTPException(400, "Requested file too big")
    return StreamingResponse(random_bytes(file_size), media_type="application/octet-stream",
                             headers={"Content-Length": f"{file_size}"})
