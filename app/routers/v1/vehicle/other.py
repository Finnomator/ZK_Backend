import os

from fastapi import APIRouter, Request, Response

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


@router.post("/up-down-test")
async def up_and_download_test(request: Request):
    body = await request.body()
    return Response(status_code=200, content=body)
