import httpx
import json
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
