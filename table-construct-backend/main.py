"""
FastAPI 主应用文件
实现表格查询接口和文件上传接口
"""

import logging
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import (
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    HOST,
    PORT,
    BACKLOG,
    TIMEOUT_KEEP_ALIVE,
)
from database import init_all
from routers import query, upload, export

# 创建应用日志记录器
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    在应用启动时初始化依赖，在应用关闭时清理资源
    """
    # 启动时执行
    logger.info("应用启动，开始初始化依赖...")
    try:
        success = init_all()
        if success:
            logger.info("所有依赖初始化成功")
        else:
            logger.error("部分依赖初始化失败，请检查日志")
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        raise
    
    try:
        yield
    except asyncio.CancelledError:
        # 正常关闭时的取消错误，可以忽略
        logger.info("应用正在关闭...")
        raise
    except Exception as e:
        logger.error(f"应用运行期间发生错误: {e}", exc_info=True)
        raise
    finally:
        # 关闭时执行（如果需要清理资源）
        try:
            logger.info("应用关闭，清理资源...")
            # 这里可以添加资源清理代码
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}", exc_info=True)


# 创建 FastAPI 应用实例，使用 lifespan 事件处理器
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# 添加 CORS 中间件，允许前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(query.router)
app.include_router(upload.router)
app.include_router(export.router)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """健康检查端点"""
    return {"status": "healthy"}


@app.get("/")
async def root() -> Dict[str, str]:
    """根路径，返回 API 信息"""
    return {
        "message": "Table Construct System API",
        "version": APP_VERSION,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    import platform

    # Windows 上使用多进程会有问题（sentence_transformers 等库的导入问题）
    # 在 Windows 上使用单进程，在 Linux/Mac 上可以使用多进程
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Windows: 单进程模式，避免多进程导入问题
        logger.info("检测到 Windows 系统，使用单进程模式")
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            reload=False,  # 开发模式启用自动重载
            reload_excludes=[
                "**/*.log",  # 所有日志文件
                "**/logs/**",  # logs 目录及其所有内容
                "**/*.pyc",  # Python 编译文件
                "**/__pycache__/**",  # Python 缓存目录
                "**/chroma_db/**",  # ChromaDB 数据库文件
                "**/*.sqlite3",  # SQLite 数据库文件
                "**/*.bin",  # 二进制文件
            ],
            reload_delay=0.5,  # 延迟0.5秒再重载，减少频繁触发
            backlog=BACKLOG,
            timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
            log_level="info",
        )
    else:
        # Linux/Mac: 可以使用多进程
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        workers = max(4, min(cpu_count, 8))
        logger.info(f"检测到 {platform.system()} 系统，使用 {workers} 个工作进程")
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            workers=workers,
            reload=False,  # 开发模式启用自动重载
            reload_excludes=[
                "**/*.log",  # 所有日志文件
                "**/logs/**",  # logs 目录及其所有内容
                "**/*.pyc",  # Python 编译文件
                "**/__pycache__/**",  # Python 缓存目录
                "**/chroma_db/**",  # ChromaDB 数据库文件
                "**/*.sqlite3",  # SQLite 数据库文件
                "**/*.bin",  # 二进制文件
            ],
            reload_delay=0.5,  # 延迟0.5秒再重载，减少频繁触发
            backlog=BACKLOG,
            timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
            log_level="info",
        )
