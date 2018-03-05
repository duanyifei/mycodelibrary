# coding=utf-8
"""
日志模块
默认为 logging.handlers.RotatingFileHandler
支持json格式的日志记录

"""
import os
import sys
import logging
import logging.handlers

current_file_path = os.path.dirname(os.path.abspath(sys.path[0]))
log_path = os.path.join(current_file_path, "log")

if not os.path.isdir(log_path):
    os.makedirs(log_path)


def get_logger(filename):
    filename = filename.split(os.sep)[-1].split(".")[0]
    logger = logging.getLogger(filename)
    # 独立本地日志文件
    p_fp = logging.handlers.RotatingFileHandler(os.path.join(log_path, "%s.log" % filename), maxBytes=10 * 1024 * 1024,
                                                mode='a', backupCount=100)
    logger.addHandler(p_fp)

    # 综合本地日志文件
    fp = logging.handlers.RotatingFileHandler(os.path.join(log_path, "debug.log"), maxBytes=10 * 1024 * 1024, mode='a',
                                              backupCount=100)
    logger.addHandler(fp)

    # 标准输出流
    std = logging.StreamHandler(sys.stdout)
    logger.addHandler(std)

    # 定制标准输出和本地文件日志格式
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(filename)s] [%(lineno)d] - %(message)s")
    p_fp.setFormatter(formatter)
    fp.setFormatter(formatter)
    std.setFormatter(formatter)
    # logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)
    return logger


if __name__ == "__main__":
    logger = get_logger("test")
    logger.debug("hello")
