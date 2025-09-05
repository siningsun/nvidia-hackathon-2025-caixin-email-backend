import logging
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class CaixinScrapperFunctionConfig(FunctionBaseConfig, name="caixin_scrapper"):
    """
    NAT function for scraping Caixin Weekly cover articles.
    """
    date: str = Field(default="latest", description="Target date: 'latest' or 'YYYY-MM-DD'")


@register_function(config_type=CaixinScrapperFunctionConfig)
async def caixin_scrapper_function(config: CaixinScrapperFunctionConfig, builder: Builder):
    async def _response_fn(input_message: str) -> dict:
        date = config.date
        email = config.email
        password = config.password

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 1️⃣ 登录
            await page.goto("https://u.caixin.com/web/login")
            await page.fill("#email", email)
            await page.fill("#password", password)
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")

            # 2️⃣ 导航到目标期刊
            if date.lower() == "latest":
                target_url = "https://weekly.caixin.com/latest/"
            else:
                target_url = f"https://weekly.caixin.com/{date}/"

            await page.goto(target_url)
            await page.wait_for_selector(".cover-story-title")

            # 3️⃣ 抓取封面标题和文章链接
            headline = await page.text_content(".cover-story-title")
            article_url = await page.get_attribute(".cover-story-title a", "href")

            # 4️⃣ 抓取文章内容
            await page.goto(article_url)
            await page.wait_for_selector(".article-body")
            article_text = await page.text_content(".article-body")

            await browser.close()
            return {
                "date": date,
                "headline": headline,
                "url": article_url,
                "content": article_text
            }

    try:
        yield FunctionInfo.create(single_fn=_response_fn)
    except GeneratorExit:
        logger.warning("Function exited early!")
    finally:
        logger.info("Cleaning up caixin_scrapper workflow.")
