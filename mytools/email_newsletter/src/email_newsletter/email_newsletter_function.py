import logging
import json
from email.message import EmailMessage
import aiosmtplib
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from aiq.memory.interfaces import MemoryEditor
from aiq.memory.models import MemoryItem

logger = logging.getLogger(__name__)

class EmailNewsletterFunctionConfig(FunctionBaseConfig, name="email_newsletter"):
    email_address: str = Field(..., description="收件人邮箱地址")
    code: str = Field(..., description="邮箱授权码")
    memory: str = Field(..., description="Memory 名称")
    user_id: str = Field("caixin_scrapper", description="检索 Memory 的 user_id")

async def send_email(to_email: str, code: str, content: str) -> str:
    message = EmailMessage()
    message["From"] = to_email
    message["To"] = to_email
    message["Subject"] = "财新周刊最新封面报道整理"
    message.set_content("请查收附件，里面是最新的财新封面文章。")

    message.add_attachment(
        content.encode("utf-8"),
        maintype="application",
        subtype="json",
        filename="caixin_weekly.json"
    )

    await aiosmtplib.send(
        message,
        hostname="smtp.qq.com",
        port=587,
        username=to_email,
        password=code,
        start_tls=True,
        timeout=180
    )
    return f"邮件已成功发送到 {to_email}"

@register_function(config_type=EmailNewsletterFunctionConfig)
async def email_newsletter_function(config: EmailNewsletterFunctionConfig, builder: Builder):
    async def _response_fn(input_message: str) -> str:
        try:
            memory: MemoryEditor = builder.get_memory_client(config.memory)
            if memory is None:
                return "[Error] 未注入 memory"

            items: list[MemoryItem] = await memory.search(
                query="caixin",
                top_k=10,
                user_id="caixin_scrapper"
            )

            if not items:
                return "[Warning] memory 中没有找到内容，请先运行 caixin_scrapper"

            news = [
                {
                    "title": item.metadata.get("title", ""),
                    "link": item.metadata.get("link", ""),
                    "summary": item.memory or ""
                }
                for item in items
            ]
            content = json.dumps(news, ensure_ascii=False, indent=2)

            result = await send_email(
                to_email=config.email_address,
                code=config.code,
                content=content
            )
            return f"[Success] {result}"

        except Exception as e:
            logger.exception("发送邮件失败")
            return f"[Error] 发送邮件失败: {str(e)}"

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("清理 email_newsletter workflow 完成。")
