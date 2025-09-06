import logging
import uuid
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from aiq.memory.models import MemoryItem
from aiq.memory.interfaces import MemoryEditor
from .run_caixin_page_scrapper import CaixinSession, caixin_login, fetch_all_pages, parse_article

logger = logging.getLogger(__name__)

class CaixinScrapperFunctionConfig(FunctionBaseConfig, name="caixin_scrapper"):
    """
    NAT function for scraping Caixin Weekly cover articles without browser.
    """
    email: str = Field(..., description="Caixin account email")
    password: str = Field(..., description="Caixin account password")
    memory: str = Field("...", description="Memory for the function, if applicable.")


@register_function(config_type=CaixinScrapperFunctionConfig)
async def caixin_scrapper_function(config: CaixinScrapperFunctionConfig, builder: Builder):
    async def _response_fn(input_message: str) -> dict:
        email = config.email
        password = config.password
        memory: MemoryEditor = builder.get_memory_client(config.memory)
        session: CaixinSession = None
        try:
            # 登录
            session = await caixin_login(email, password)
            logger.info(f"Logged in as {email}")

            articles = await fetch_all_pages(total_pages=1)
            parsed = [parse_article(a) for a in articles]

            for a in parsed:
                print(f"[标题] {a['title']}")
                print(f"[链接] {a['link']}")
                print(f"[摘要] {a['summary']}")
                print(f"[时间] {a['time']}")
                print(f"[收费] {'是' if a['paid'] else '否'}")
                print("\n")

            # 写入 Memory
            if memory:
                await memory.add_items([
                    MemoryItem(
                        user_id="caixin_scrapper",
                        memory=f"{a['title']} - {a['summary']}",
                        tags=["caixin"],
                        metadata={
                            "uuid": str(uuid.uuid4()),
                            "title": a['title'],
                            "summary": a['summary'],
                            "link": a['link'],
                            "time": a['time']
                        }
                    )
                    for a in parsed
                ])
            return {"content": parsed}

        except Exception as e:
            logger.exception("Error in caixin_scrapper_function")
            return {"error": str(e)}

        finally:
            if session:
                await session.close()

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("Cleaning up caixin_scrapper workflow.")
