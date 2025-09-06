import json
import redis.asyncio as aioredis
from aiq.memory.interfaces import MemoryEditor
from aiq.memory.models import MemoryItem
from typing import Optional, Callable
import uuid

class RedisMemoryEditor(MemoryEditor):
    _type = "redis_memory"

    def __init__(self, redis_client: aioredis.Redis, namespace: str = "memory"):
        self.redis = redis_client
        self.namespace = namespace

    def _key(self, item_uuid: str) -> str:
        return f"{self.namespace}:{item_uuid}"

    async def add_items(self, items: list[MemoryItem]) -> None:
        """批量插入 MemoryItem，每条使用唯一 uuid 作为 key"""
        if not items:
            return
        pipeline = self.redis.pipeline()
        for item in items:
            key = self._key(item.metadata.get("uuid") or str(uuid.uuid4()))
            pipeline.set(key, json.dumps(item.dict()))
        await pipeline.execute()

    async def search(self, query: str, top_k: int = 5, user_id: str = None) -> list[MemoryItem]:
        """简单全文匹配 memory 或 metadata"""
        keys = await self.redis.keys(f"{self.namespace}:*")
        results = []
        for key in keys:
            raw = await self.redis.get(key)
            if raw is None:
                continue
            try:
                data = json.loads(raw)
                item = MemoryItem(**data)
                if user_id and item.user_id != user_id:
                    continue
                text_to_search = item.memory or ""
                if query.lower() in text_to_search.lower() or query.lower() in str(item.metadata).lower():
                    results.append(item)
            except Exception:
                continue
        return results[:top_k]

    async def remove_items(self, criteria: Optional[Callable[[MemoryItem], bool]] = None, **kwargs) -> None:
        keys = await self.redis.keys(f"{self.namespace}:*")
        pipeline = self.redis.pipeline()
        for key in keys:
            raw = await self.redis.get(key)
            if raw is None:
                continue
            try:
                item = MemoryItem(**json.loads(raw))
                if criteria is None or criteria(item):
                    pipeline.delete(key)
            except Exception:
                continue
        await pipeline.execute()
