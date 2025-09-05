import asyncio
import httpx
import json
from typing import List, Dict
from bs4 import BeautifulSoup
from typing import Optional
import re

class CaixinSession:
    """封装登录返回的 code，用于后续 API 调用"""
    def __init__(self, uid: str, login_code: str):
        self.uid = uid
        self.login_code = login_code
        self.client = httpx.AsyncClient()

    async def get(self, url: str, params: dict = None, **kwargs):
        if params is None:
            params = {}
        params['code'] = self.login_code
        response = await self.client.get(url, params=params, **kwargs)
        return response

    async def post(self, url: str, data: dict = None, json_data: dict = None, **kwargs):
        if data is None:
            data = {}
        data['code'] = self.login_code
        response = await self.client.post(url, data=data, json=json_data, **kwargs)
        return response

    async def close(self):
        await self.client.aclose()

async def caixin_login(account: str, password: str) -> CaixinSession:
    url = "https://gateway.caixin.com/api/ucenter/user/v1/loginJsonp"
    params = {
        "account": account,
        "password": password,
        "deviceType": 5,
        "unit": 1,
        "device": "CaixinWebsite",
        "userTag": "undefined",
        "extend": '{"resource_article":""}',
        "callback": "__caixincallback123456"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        m = re.search(r'__caixincallback\d+\((.*)\)', resp.text)
        if not m:
            raise ValueError("登录返回数据格式异常")
        data = json.loads(m.group(1))
        if data.get("code") != 0:
            raise ValueError(f"登录失败: {data.get('msg')}")

        login_data = data["data"]
        uid = login_data["uid"]
        login_code = login_data["code"]

        return CaixinSession(uid=uid, login_code=login_code)


BASE_URL = "https://gateway.caixin.com/api/extapi/homeInterface.jsp"
PAGE_SIZE = 5 # 每页文章数量

async def fetch_page(client: httpx.AsyncClient, start: int) -> List[Dict]:
    """
    抓取单页文章列表
    """
    params = {
        "callback": "?",
        "subject": "100689028",  # 周刊封面报道
        "type": "0",
        "count": PAGE_SIZE,
        "picdim": "_266_177",
        "start": start
    }
    resp = await client.get(BASE_URL, params=params)
    text = resp.text
    # 去掉 JSONP 包裹 ?( ... )
    json_str = text[text.find("(")+1 : text.rfind(")")]
    data = json.loads(json_str)
    return data.get("datas", [])

async def fetch_all_pages(total_pages: int = 2) -> List[Dict]:
    """
    抓取多页文章
    """
    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [fetch_page(client, start=i*PAGE_SIZE) for i in range(total_pages)]
        results = await asyncio.gather(*tasks)
    # flatten
    articles = [item for page in results for item in page]
    return articles

def parse_article(item: Dict) -> Dict:
    """
    提取我们关心的字段
    """
    return {
        "title": item.get("desc"),
        "link": item.get("link"),
        "summary": item.get("summ"),
        "time": item.get("time"),
        "paid": item.get("attr") != 0  # True 表示收费
    }

async def fetch_article_body(client: httpx.AsyncClient, article_url: str) -> str:
    try:
        resp = await client.get(article_url)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        return f"[请求失败: {e}]"

    soup = BeautifulSoup(resp.text, "html.parser")

    # body
    body = soup.select_one("body")
    print(body.name if body else "body not found")
    # print(body)
    # div.main-all
    main_all = soup.select_one("div.main-all")
    print(main_all.name if main_all else "div.main-all not found")

    # div#cons.cons
    cons_div = soup.select_one("div#cons.cons")
    print(cons_div.name if cons_div else "div#cons.cons not found")

    # article
    article = soup.select_one("article#Main_Content_Val.news-con")
    print(article.name if article else "article#Main_Content_Val.news-con not found")

    # Step 1: 从明确结构中提取 article 标签
    container = soup.select_one("div.main-all > div#cons.cons > article#Main_Content_Val.news-con")
    if not container:
        return "[未找到正文容器：article]"

    # Step 2: 提取所有段落
    paragraphs = container.find_all("p", recursive=True)

    # Step 3: 清洗文本内容
    text_list = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        if not text:
            continue
        if any(keyword in text for keyword in ["责任编辑", "阅读更多", "本文为", "未经许可", "版权所有"]):
            continue
        text_list.append(text)
    
    print(f"提取到 {len(text_list)} 段正文")
    print(f"正文预览: {text_list[:3]}...")  # 打印前三段看看
    return "\n".join(text_list) if text_list else "[正文为空或不可访问]"



async def main():
    articles = await fetch_all_pages(total_pages=1)
    parsed = [parse_article(a) for a in articles]
    
    async with httpx.AsyncClient(timeout=10) as client:
        for a in parsed:
            print(f"[标题] {a['title']}")
            print(f"[链接] {a['link']}")
            print(f"[摘要] {a['summary']}")
            print(f"[时间] {a['time']}")
            print(f"[收费] {'是' if a['paid'] else '否'}")
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())
