import sys, os, traceback

try:
    from app.main import app
except Exception as e:
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/{path:path}")
    @app.get("/")
    async def catch_all(path: str = ""):
        tb = traceback.format_exc()
        return {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": tb[-500:]
        }
