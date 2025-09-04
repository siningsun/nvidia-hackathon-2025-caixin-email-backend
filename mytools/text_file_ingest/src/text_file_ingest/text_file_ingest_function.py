from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from .embedder.aliyun_balian_embedder import AliyunBailianEmbedder
from nat.builder.framework_enum import LLMFrameworkEnum

# 初始化 builder
builder = Builder()

# 注册阿里云百炼 embedder
builder.register_embedder(
    name="text-embedding-v4",
    embedder_class=AliyunBailianEmbedder,
    framework=LLMFrameworkEnum.LANGCHAIN,
    api_key="sk-1014201923ec4d189b8ebad8c99adbc5"
)

import logging

from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class TextFileIngestFunctionConfig(FunctionBaseConfig, name="text_file_ingest"):
    """
    NAT function template. Please update the description.
    """
    # Add your custom configuration parameters here
    ingest_glob: str = Field(
        ...,
        description="Glob pattern to match text files for ingestion.",
        example="data/*.txt",
    )
    description: str = Field(
        "Ingest text files and make their content searchable.",
        description="Description of the text file ingestion function.",
    )
    chunk_size: int = Field(
        1024,
        description="Size of text chunks to split the files into.",
        example=1024,
    )
    embedder_name: str = Field(
        "nvidia/nv-embedqa-e5-v5",
        description="Name of the embedder to use for text embedding.",
        example="nvidia/nv-embedqa-e5-v5",
    )


@register_function(config_type=TextFileIngestFunctionConfig)
async def text_file_ingest_function(
    config: TextFileIngestFunctionConfig, builder: Builder
):
    from langchain.tools.retriever import create_retriever_tool
    from langchain_community.document_loaders import DirectoryLoader
    from langchain_community.document_loaders import TextLoader
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import os
    from langchain_core.embeddings import Embeddings
    
    embeddings: Embeddings = await builder.get_embedder(config.embedder_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    logger.info("Ingesting documents matching for the webpage: %s", config.ingest_glob)

    (ingest_dir, ingest_glob) = os.path.split(config.ingest_glob)
    loader = DirectoryLoader(ingest_dir, glob=ingest_glob, loader_cls=TextLoader)

    docs = [document async for document in loader.alazy_load()]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=config.chunk_size)
    documents = text_splitter.split_documents(docs)
    vector = await FAISS.afrom_documents(documents, embeddings)

    retriever = vector.as_retriever()

    retriever_tool = create_retriever_tool(
        retriever,
        "text_file_ingest",
        config.description,
    )

    async def _inner(query: str) -> str:
        return await retriever_tool.arun(query)
    
    yield FunctionInfo.from_fn(_inner, description=config.description)