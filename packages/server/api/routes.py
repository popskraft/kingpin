from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {
        "ok": True,
        "service": "KINGPIN 2P Server",
        "health": "/health",
        "socket_io": "/socket.io/",
    }


@router.get("/health")
async def health():
    return {"ok": True}

