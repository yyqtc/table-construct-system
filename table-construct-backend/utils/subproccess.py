import shlex
import subprocess
import platform
import logging

logger = logging.getLogger(__name__)

def _execute_script_subprocess(script_command, env_vars=None) -> str:
    """
    使用 subprocess 模块执行脚本（推荐）

    Args:
        script_command: 要执行的命令字符串
        env_vars: 要传递的环境变量字典，例如 {"CURSOR_API_KEY": "..."}
    """
    try:
        # 检测操作系统
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            # Windows 使用 cmd /c
            full_command = ""
            if env_vars:
                env_exports = " && ".join(
                    [f"set {k}={shlex.quote(str(v))}" for k, v in env_vars.items()]
                )
                full_command = f"{env_exports} && {script_command}"
            else:
                full_command = f"{script_command}"
            
            result = subprocess.run(
                ["cmd", "/c", full_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
        else:
            # Linux/Unix 使用 bash -c
            full_command = ""
            if env_vars:
                env_exports = " ".join(
                    [f"export {k}={shlex.quote(str(v))}" for k, v in env_vars.items()]
                )
                full_command = f"{env_exports} && {script_command}"
            else:
                full_command = f"{script_command}"
            
            result = subprocess.run(
                ["bash", "-c", full_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"执行脚本失败: {e}")
        return "执行失败！"
    except Exception as e:
        logger.error(f"执行脚本失败: {e}")
        return "执行失败！"
