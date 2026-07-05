from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message


class HistoryRepository(Protocol):
    """Storage interface for conversation history.

    The routers depend on this interface only, so the backend can be swapped
    (for example to AgentCore-native session storage) without touching them.
    """

    async def list_conversations(self, user_id: str) -> list[Conversation]: ...

    async def get_conversation(self, user_id: str, conversation_id: str) -> Conversation | None: ...

    async def create_conversation(self, user_id: str, agent_id: str, title: str) -> Conversation: ...

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_events: Any | None = None,
    ) -> Message: ...

    async def touch_conversation(self, conversation_id: str, title: str | None = None) -> None: ...


class SqlAlchemyHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_conversations(self, user_id: str) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation(self, user_id: str, conversation_id: str) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        result = await self._session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is not None:
            await self._session.refresh(conversation, attribute_names=["messages"])
        return conversation

    async def create_conversation(self, user_id: str, agent_id: str, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, agent_id=agent_id, title=title)
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_events: Any | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_events_json=tool_events,
        )
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def touch_conversation(self, conversation_id: str, title: str | None = None) -> None:
        conversation = await self._session.get(Conversation, conversation_id)
        if conversation is None:
            return
        if title:
            conversation.title = title
        self._session.add(conversation)
        await self._session.commit()
