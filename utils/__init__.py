"""工具函数模块"""

try:
    from .logger import get_logger, setup_logging
except ImportError:
    from utils.logger import get_logger, setup_logging

__all__ = ["get_logger", "setup_logging"]
