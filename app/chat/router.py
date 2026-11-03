from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import conversations
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.chat import service
from app.chat.enums import MessageRole
from app.chat.llm import get_client
from app.chat.schemas import BurnedTokensResponse, ConversationResponse, CreateConversationRequest, MessageResponse, SendMessageRequest, ToolCallResponse, UpdateConversationRequest
from app.chat.service import get_owned_conversation
from app.db.database import get_db
from app.db.models import Conversation, Message


router = APIRouter()

# create a conversation
@router.post("/create", response_model=ConversationResponse , status_code=201)
def create_conversation(request: CreateConversationRequest, db: Session = Depends(get_db), User: UserResponse = Depends(get_current_user)):
    title = request.title
    client = get_client("llama-3.1-8b-instant")
    response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {
            "role": "system",
            "content": "You generate concise conversation titles."
        },
        {
            "role": "user",
            "content": f"""
Generate a short title for this conversation based ONLY on the user's first message.

First message:
{title}

Rules:
- Maximum 8 words.
- Capture the main topic.
- Use title case.
- Do not use quotes.
- Do not add punctuation at the end.
- Return ONLY the title.
"""
        }
    ]
)
    # ai_generated_title = 
    conversation = (Conversation(title=response.choices[0].message.content, user_id=User.id, model=request.model))
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

# delete a conversation

@router.delete("/delete/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db), User: UserResponse = Depends(get_current_user)):
    conversation = get_owned_conversation(db, conversation_id, User.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}

# get all conversations

@router.get("/all", response_model=list[ConversationResponse])
def get_all_conversations(db: Session = Depends(get_db), User: UserResponse = Depends(get_current_user)):
    conversations = db.query(Conversation).where(Conversation.user_id == User.id).all()
    return conversations

# update a conversation

@router.patch("/update/{conversation_id}", response_model=ConversationResponse)
def update_conversation(conversation_id: int, request: UpdateConversationRequest, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updates = request.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(conversation, key, value)
    db.commit()
    db.refresh(conversation)
    return conversation

# get all messages for a conversation

@router.get("/messages/{conversation_id}", response_model=list[MessageResponse])
def get_messages(conversation_id: int, db: Session = Depends(get_db), User: UserResponse = Depends(get_current_user)):
    conversation = get_owned_conversation(db, conversation_id, User.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation.messages

# send a message to a conversation

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: int, request: SendMessageRequest, db: Session = Depends(get_db), User: UserResponse = Depends(get_current_user)):
    conversation = get_owned_conversation(db, conversation_id, User.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    generator = await service.stream_reply(db, conversation, request.message,  User.id,request.temperature,)
    return StreamingResponse(generator, media_type="text/event-stream")

# get the burned tokens for a user

@router.get("/burned_tokens", response_model=BurnedTokensResponse)
def get_burned_tokens(db:Session = Depends(get_db), User:UserResponse = Depends(get_current_user)):
    conversations = db.query(Conversation).where(Conversation.user_id == User.id).all()
    total_tokens = 0
    for conversation in conversations:
        for message in conversation.messages:
            total_tokens += message.total_tokens
    return BurnedTokensResponse(tokens=total_tokens)

@router.post("/tools", response_model=ToolCallResponse)
async def chat_with_tools_api(request:SendMessageRequest ):
    response = await service.chat_with_tools(request.message)

    return ToolCallResponse(content=response)