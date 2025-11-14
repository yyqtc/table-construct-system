"""
数据库和模型初始化
"""

import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, VECTOR_MODEL_NAME

logger = logging.getLogger(__name__)

# 全局变量
chroma_client = None
collection = None
model = None


def init_chromadb():
    """初始化 ChromaDB 客户端"""
    global chroma_client, collection
    try:
        chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH, settings=Settings(anonymized_telemetry=False)
        )
        collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        logger.info("ChromaDB初始化成功")
        return True
    except Exception as e:
        logger.error(f"ChromaDB初始化失败: {e}", exc_info=True)
        chroma_client = None
        collection = None
        return False


def init_vector_model():
    """初始化向量模型"""
    global model
    try:
        model = SentenceTransformer(VECTOR_MODEL_NAME)
        logger.info("向量模型初始化成功")
        return True
    except Exception as e:
        logger.error(f"向量模型初始化失败: {e}", exc_info=True)
        model = None
        return False


def init_all():
    """初始化所有依赖"""
    chromadb_ok = init_chromadb()
    model_ok = init_vector_model()
    return chromadb_ok and model_ok


def get_collection():
    """获取 ChromaDB collection"""
    return collection


def get_model():
    """获取向量模型"""
    return model
