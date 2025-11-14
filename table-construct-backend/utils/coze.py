from cozepy import COZE_CN_BASE_URL, AsyncCoze, AsyncTokenAuth, Coze, TokenAuth
from config import COZE_API_TOKEN

import os

coze_api_base = os.getenv("COZE_API_BASE") or COZE_CN_BASE_URL

async_coze = AsyncCoze(auth=AsyncTokenAuth(token=COZE_API_TOKEN), base_url=coze_api_base)

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

