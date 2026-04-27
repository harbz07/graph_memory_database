import asyncio
import os
from datetime import datetime, timedelta

from mem0 import AsyncMemoryClient

MEM0_API_KEY = os.getenv("MEM0_API_KEY", "your-mem0-api-key-here")
client = AsyncMemoryClient(api_key=MEM0_API_KEY)
APP_ID = "soulOS-biomimetic-core"


async def meta_cognitive_gate(content: str) -> str:
    # Insert your NeMo-trained NIM upstream filter here.
    # If the input is conversational garbage, return None and summarily execute the memory.
    if len(content.strip()) < 10 or "just checking in" in content.lower():
        return None
    return content


def get_ephemeral_decay() -> str:
    # Insert RL model logic here for dynamic half-life.
    # Defaulting to a 7-day decay so the graph doesn't choke on outdated shit.
    return (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"


async def write_memory(
    content: str, agent_id: str, user_id: str, metadata: dict = None
):
    distilled_content = await meta_cognitive_gate(content)
    if not distilled_content:
        return None

    meta = metadata or {}
    meta["expiration_date"] = get_ephemeral_decay()

    # Fast path: Dump into vector store instantly.
    await client.add(
        distilled_content,
        user_id=user_id,
        agent_id=agent_id,
        app_id=APP_ID,
        metadata=meta,
    )

    # Offload the heavy multi-hop graph extraction to the background.
    asyncio.create_task(
        client.add(
            distilled_content,
            user_id=user_id,
            agent_id=agent_id,
            app_id=APP_ID,
            enable_graph=True,
            metadata=meta,
        )
    )


async def search_vault(query: str, user_id: str, top_k: int = 5):
    # Pulling from the vault using the proper downstream distillation.
    return await client.search(
        query,
        user_id=user_id,
        app_id=APP_ID,
        limit=top_k,
        rerank=True,
        filter_memories=True,
    )
