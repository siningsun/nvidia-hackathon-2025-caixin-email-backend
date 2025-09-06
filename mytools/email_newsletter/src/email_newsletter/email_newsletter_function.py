import logging
from email.message import EmailMessage
import aiosmtplib
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
import json

logger = logging.getLogger(__name__)


class EmailNewsletterFunctionConfig(FunctionBaseConfig, name="email_newsletter"):
    class Config:
        title = "email_newsletter"
    email_address: str = Field(..., description="收件人邮箱地址")
    code: str = Field(..., description="邮箱授权码")
    content: str = Field(..., description="邮件正文内容或 JSON 字符串")


async def send_email(to_email: str, code: str, content: str) -> str:
    """
    content: 可以是纯文本，也可以是 JSON 字符串
    自动生成 HTML 邮件正文 + JSON 附件
    """
    print("[DEBUG] 收到 content:", repr(content))
    # 尝试解析 JSON，如果不是 JSON 就直接当作文本
    try:
        json_content = json.loads(content)
        attachment_content = json.dumps(json_content, ensure_ascii=False, indent=2)
    except Exception:
        attachment_content = content

    # 构建邮件
    message = EmailMessage()
    message["From"] = to_email
    message["To"] = to_email
    message["Subject"] = "财新周刊最新封面报道整理"
    message.set_content(
        "请查收附件，里面是最新的财新周刊封面报道整理。"
    )

    # 添加附件
    message.add_attachment(
        attachment_content.encode("utf-8"),
        maintype="application",
        subtype="json",
        filename="caixin_weekly.json",
    )

    # 发送邮件
    await aiosmtplib.send(
        message,
        hostname="smtp.qq.com",
        port=587,
        username=to_email,
        password=code,
        start_tls=True,
        timeout=180,
    )

    return f"邮件已成功发送到 {to_email}"


@register_function(config_type=EmailNewsletterFunctionConfig)
async def email_newsletter_function(config: EmailNewsletterFunctionConfig, builder: Builder):
    async def _response_fn(input_message: str) -> str:
        try:
            result = await send_email(
                to_email=config.email_address,
                code=config.code,
                content=config.content
            )
            return f"[Success] {result}"
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return f"[Error] 发送邮件失败: {str(e)}"

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited早退!")
    finally:
        logger.info("清理 email_newsletter workflow 完成。")
