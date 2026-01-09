import os
import time

from loguru import logger

loggers = {}


def get_log_path(business_name, level="info") -> str:
    """
    根据业务名+等级+日期 生成日志文件名
    需要传入 业务名 和 日志等级
    """
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(basedir, 'logs')

    if not os.path.exists(log_path):
        os.makedirs(log_path, exist_ok=True)

    time_str = time.strftime("%Y-%m-%d")
    log_file = f"{business_name}_{level}_{time_str}.log"
    log_path = os.path.join(log_path, log_file)

    return log_path


def get_logger(name: str) -> logger:
    """
    获取日志记录器
    """
    if name in loggers:
        return loggers[name]

    # 创建一个新的日志记录器
    new_logger = logger.bind(name=name)

    new_logger.add(
        get_log_path(name, 'INFO'),  # 生成日志文件名
        rotation="12:00",  # 每天12点分割
        retention="5 days",  # 保留5天
        enqueue=True,  # 异步写入
        encoding='utf-8',  # 编码格式
        filter=lambda record: record["extra"].get("name") == name  # 过滤器，对业务进行区分记录
    )

    new_logger.add(
        get_log_path(name, 'ERROR'),
        rotation="12:00",
        retention="5 days",
        level='ERROR',  # 只记录错误
        enqueue=True,
        encoding='utf-8',
        filter=lambda record: record["extra"].get("name") == name
    )

    loggers[name] = new_logger
    return new_logger
