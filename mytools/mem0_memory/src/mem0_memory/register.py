from aiq.builder.builder import Builder
from aiq.cli.register_workflow import register_memory
from aiq.data_models.memory import MemoryBaseConfig
from aiq.data_models.retry_mixin import RetryMixin
from aiq.utils.exception_handlers.automatic_retries import patch_with_retry
from .redis_editor import RedisMemoryEditor
import redis.asyncio as aioredis

class RedisMemoryConfig(MemoryBaseConfig, RetryMixin, name="redis_memory"):
    url: str = "redis://localhost:6379/0"  # 默认本地 Redis
    db: int = 0

@register_memory(config_type=RedisMemoryConfig)
async def redis_memory_client(config: RedisMemoryConfig, builder: Builder):
    redis_client = aioredis.from_url(config.url, db=config.db, decode_responses=True)

    from .redis_editor import RedisMemoryEditor
    memory_editor = RedisMemoryEditor(redis_client)

    if isinstance(config, RetryMixin):
        memory_editor = patch_with_retry(
            memory_editor,
            retries=config.num_retries,
            retry_codes=config.retry_on_status_codes,
            retry_on_messages=config.retry_on_errors,
        )

    yield memory_editor
