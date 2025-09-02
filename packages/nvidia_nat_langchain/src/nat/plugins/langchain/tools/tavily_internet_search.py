# SPDX-FileCopyrightText: Copyright (c) 2024-2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

import os
import aiohttp
from langchain_tavily import TavilySearch


# Internet Search tool configuration
class TavilyInternetSearchToolConfig(FunctionBaseConfig, name="tavily_internet_search"):
    """
    Tool that retrieves relevant contexts from web search (using Tavily) for the given question.
    Requires a TAVILY_API_KEY.
    """
    max_results: int = 3
    api_key: str = ""


@register_function(config_type=TavilyInternetSearchToolConfig)
async def tavily_internet_search(tool_config: TavilyInternetSearchToolConfig, builder: Builder):
    # 设置 API Key
    if not os.environ.get("TAVILY_API_KEY") and tool_config.api_key:
        os.environ["TAVILY_API_KEY"] = tool_config.api_key

    # 创建 TavilySearch 实例
    tavily_search = TavilySearch(max_results=tool_config.max_results)

    async def _tavily_internet_search(question: str) -> str:
        # 使用 aiohttp 忽略 SSL 验证（仅本地开发可用）
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            search_docs = await tavily_search.ainvoke({'query': question}, session=session)

        # 调试输出
        print("search_docs:", search_docs)
        print("type(search_docs):", type(search_docs))

        # 兼容返回类型
        if isinstance(search_docs, str):
            # 字符串直接包装为 Document
            web_search_results = f"<Document>{search_docs}</Document>"
        elif isinstance(search_docs, list):
            # 列表每项可能是 dict 或字符串
            web_search_results = "\n\n---\n\n".join(
                [
                    f'<Document href="{doc.get("url", "#")}"/>\n{doc.get("content", doc)}\n</Document>'
                    if isinstance(doc, dict) else f"<Document>{doc}</Document>"
                    for doc in search_docs
                ]
            )
        else:
            # 防御性处理
            web_search_results = f"<Document>{str(search_docs)}</Document>"

        return web_search_results

    # 注册为 NAT 可调用工具
    yield FunctionInfo.from_fn(
        _tavily_internet_search,
        description=(
            """This tool retrieves relevant contexts from web search (using Tavily) for the given question.

            Args:
                question (str): The question to be answered.
            """
        ),
    )
