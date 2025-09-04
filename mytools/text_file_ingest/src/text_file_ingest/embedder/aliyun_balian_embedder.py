from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.builder import BaseEmbedder
import dashscope
from http import HTTPStatus

class AliyunBailianEmbedder(BaseEmbedder):
    """
    NAT 自定义 embedder：调用阿里云百炼文本嵌入模型。
    """

    def __init__(self, model_name: str = "text_embedding_v4", **kwargs):
        self.model_name = model_name
        dashscope.api_key = kwargs.get("api_key")  # 通过 kwargs 传入 API Key

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        texts: list of strings
        返回 list of embeddings
        """
        embeddings_list = []
        for text in texts:
            response = dashscope.TextEmbedding.call(
                model=self.model_name,
                input=text
            )
            if response.status_code != HTTPStatus.OK:
                raise RuntimeError(f"调用阿里云百炼 embedder 失败: {response.status_code}, {response.message}")
            embeddings_list.append(response.output['embeddings'][0]['embedding'])
        return embeddings_list
