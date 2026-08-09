import asyncio

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.conversation import Conversation


async def main():
    async with async_session_factory() as session:
        result = await session.execute(
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )

        conversation = result.scalar_one()

        print("Conversation ID:", conversation.id)
        print("User ID:", conversation.user_id)
        print("Title:", conversation.title)


asyncio.run(main())