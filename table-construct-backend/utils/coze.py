from cozepy import COZE_CN_BASE_URL, AsyncCoze, AsyncTokenAuth

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径（用于直接运行此文件时）
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import COZE_API_TOKEN, COZE_CHECK_TABLE_API_TOKEN

coze_api_base = os.getenv("COZE_API_BASE") or COZE_CN_BASE_URL

async_coze = AsyncCoze(auth=AsyncTokenAuth(token=COZE_API_TOKEN), base_url=coze_api_base)

async_check_coze = AsyncCoze(auth=AsyncTokenAuth(token=COZE_CHECK_TABLE_API_TOKEN), base_url=coze_api_base)

# xml_to_html_template = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         """
#         你是一个优秀的助手，最擅长根据一段xml内容，将其转换为格式尽可能接近原来word表格的html内容。

#         注意！
#         你只需要返回html内容，不要返回任何其他内容。
#         """
#     ),
#     ("user", "{raw_xml}")
# ])

xml_to_html_chain = None


async def test_coze():
    response = await async_coze.workflows.runs.create(
        workflow_id="7572136118511714304",
        parameters={
            "table_content": "Hello, world!"
        }
    )
    print(response.data)

if __name__ == "__main__":
    asyncio.run(test_coze())

