"""
应用配置文件
"""

import logging
import logging.handlers
from pathlib import Path

# 日志配置
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 创建按日期分割的文件处理器
log_file_path = LOG_DIR / "app.log"
file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=str(log_file_path),
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# 创建错误日志处理器（只记录错误）
error_log_file_path = LOG_DIR / "error.log"
error_file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=str(error_log_file_path),
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8",
)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(error_file_handler)

# 抑制第三方库的日志输出
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("docx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

# 应用配置
APP_TITLE = "Table Construct System API"
APP_DESCRIPTION = "表格构建系统后端 API"
APP_VERSION = "0.1.0"

# ChromaDB 配置
CHROMA_DB_PATH = "your_chroma_db_path"
CHROMA_COLLECTION_NAME = "your_chroma_collection_name"

# 向量模型配置
VECTOR_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# 文件上传配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# 服务器配置
HOST = "0.0.0.0"
PORT = 3000
BACKLOG = 2048
TIMEOUT_KEEP_ALIVE = 75

# Coze API 配置
COZE_API_TOKEN = "your_coze_api_token"
COZE_SUMMARY_TABLE_WORKFLOW_ID = "your_summary_table_workflow_id"
COZE_EXTRACT_PARA_WORKFLOW_ID = "your_extract_para_workflow_id"

# Coze API 检查表格配置
COZE_CHECK_TABLE_API_TOKEN = "your_check_table_api_token"
COZE_CHECK_TABLE_WORKFLOW_ID = "your_check_table_workflow_id"

# MongoDB 配置
MONGODB_URI = "your_mongodb_uri"
MONGODB_DATABASE = "your_mongodb_database"
MONGODB_STYLE_COLLECTION = "your_style_collection_name"
MONGODB_CHECK_RESULT_COLLECTION = "your_check_result_collection_name"

# PDF 配置
SOFFICE_PATH = "your_soffice_path"
PDF_DIR_PATH = "your_pdf_dir_path"
