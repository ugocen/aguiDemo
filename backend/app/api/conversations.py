from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.entra import Principal, get_current_principal
from app.db.repository import SqlAlchemyHistoryRepository
from app.db.session import get_session

router = APIRouter(tags=["conversations"])


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    tool_events_json: list | dict | None = None
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    user_id: str
    agent_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class CreateConversationIn(BaseModel):
    agent_id: str
    title: str = "New conversation"


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationOut]:
    repo = SqlAlchemyHistoryRepository(session)
    conversations = await repo.list_conversations(principal.user_id)
    return [ConversationOut.model_validate(c, from_attributes=True) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> ConversationDetail:
    repo = SqlAlchemyHistoryRepository(session)
    conversation = await repo.get_conversation(principal.user_id, conversation_id)
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return ConversationDetail.model_validate(conversation, from_attributes=True)


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationIn,
    principal: Principal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_session),
) -> ConversationOut:
    repo = SqlAlchemyHistoryRepository(session)
    conversation = await repo.create_conversation(principal.user_id, body.agent_id, body.title)
    return ConversationOut.model_validate(conversation, from_attributes=True)
