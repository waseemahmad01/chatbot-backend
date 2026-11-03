from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.database import engine
from app.db.models import Base
from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.events.router import router as event_router
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Add all models to DB if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(CORSMiddleware,allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(event_router, prefix="/events", tags=["events"])
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

@app.get("/health-check")
def root():
    return {"message":"Health Check"}

@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    print(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})