from datetime import datetime
from sqlalchemy import JSON, Integer, String, Text, ForeignKey
from sqlalchemy.orm import  Mapped, mapped_column, DeclarativeBase, relationship

from app.chat.enums import MessageRole

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] 
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(order_by="Message.id", cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column( default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column( default=datetime.now, onupdate=datetime.now)
    model: Mapped[str] = mapped_column(String(255), default="llama-3.1-70b-versatile")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    role: Mapped[MessageRole] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
    model: Mapped[str] = mapped_column(String(255), default="None")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    tool_call_id: Mapped[str] = mapped_column(String(255), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=True)
    message_type: Mapped[str] = mapped_column(String(30), default="message")