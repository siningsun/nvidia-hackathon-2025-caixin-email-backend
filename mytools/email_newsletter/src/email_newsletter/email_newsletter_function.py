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
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNewsletterFunctionConfig(FunctionBaseConfig, name="email_newsletter"):
    email_address: str = Field(..., description="收件人邮箱地址")
    code: str = Field(..., description="邮箱授权码")
    memory: str = Field(..., description="Memory 名称")
    user_id: str = Field("caixin_scrapper", description="检索 Memory 的 user_id")

import html

def json_to_html(news: list[dict]) -> str:
    """将 news 列表转换成 HTML 卡片风格"""
    html_content = """
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50;">财新周刊最新封面报道</h2>
    """
    print(news)
    for item in news:
        title = html.escape(item.get('title', ''))
        link = html.escape(item.get('link', '#'))
        summary = html.escape(item.get('summary', ''))
        html_content += f"""
        <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 8px; background-color: #f9f9f9;">
          <h3 style="margin: 0 0 5px 0;"><a href="{link}" style="text-decoration: none; color: #2980b9;">{title}</a></h3>
          <p style="margin: 0;">{summary}</p>
        </div>
        """

    html_content += """
      </body>
    </html>
    """
    return html_content


async def send_email_html(to_email: str, code: str, html_content: str) -> str:
    message = EmailMessage()
    message["From"] = to_email
    message["To"] = to_email
    message["Subject"] = "财新周刊最新封面报道整理"

    # HTML 正文
    message.add_alternative(html_content, subtype="html")

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
                top_k=5,
                user_id=config.user_id
            )

            if not items:
                return "[Warning] memory 中没有找到内容，请先运行 caixin_scrapper"

            news = [
                {
                    "title": item.metadata.get("title", ""),
                    "link": item.metadata.get("link", ""),
                    "summary": item.metadata.get("summary", ""),
                    "time": item.metadata.get("time", "")
                }
                for item in items
            ]
            # ✅ 时间排序（降序，最新在前）
            news.sort(
                key=lambda x: datetime.strptime(x["time"], "%Y-%m-%d %H:%M:%S") if x["time"] else datetime.min,
                reverse=True
            )

            html_content = json_to_html(news)
            result = await send_email_html(
                to_email=config.email_address,
                code=config.code,
                html_content=html_content
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
