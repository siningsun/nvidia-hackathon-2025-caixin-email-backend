import httpx
import json, re
import asyncio

async def login():
    url = "https://gateway.caixin.com/api/ucenter/user/v1/loginJsonp"
    params = {
        "account": "690058381@qq.com",
        "password": "oEzDudOAMZTh5y12Pgj%2FaQ%3D%3D",
        "deviceType": 5,
        "unit": 1,
        "device": "CaixinWebsite",
        "userTag": "undefined",
        "extend": '{"resource_article":""}',
        "callback": "__caixincallback123456"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        text = resp.text
        # 提取 JSON
        m = re.search(r'__caixincallback\d+\((.*)\)', text)
        if m:
            data = json.loads(m.group(1))
            print(data)

        print("Cookies:", client.cookies.jar)

asyncio.run(login())
