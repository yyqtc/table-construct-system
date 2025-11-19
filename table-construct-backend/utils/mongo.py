import os
import sys
import asyncio

from pathlib import Path
from pymongo import MongoClient

# 添加项目根目录到 Python 路径（用于直接运行此文件时）
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import MONGODB_URI, MONGODB_DATABASE, MONGODB_STYLE_COLLECTION, MONGODB_CHECK_RESULT_COLLECTION

client = MongoClient(MONGODB_URI, 27017)

db = client[MONGODB_DATABASE]

style_collection = db[MONGODB_STYLE_COLLECTION]

check_result_collection = db[MONGODB_CHECK_RESULT_COLLECTION]

if __name__ == "__main__":
    result = style_collection.insert_one({
        "table_id": "123",
        "filename": "test.docx",
        "table_index": 0,
        "styles": {
            "paragraph_style": "paragraph_style",
            "table_style": "table_style",
            "run_style": "run_style",
            "cell_style": "cell_style",
        },
    })

    print(result.inserted_id)