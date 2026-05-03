import logging
import os
from config.app_config import AppConfig

def setup_logger():
    AppConfig.init_dirs()
    
    logger = logging.getLogger(AppConfig.APP_NAME)
    logger.setLevel(getattr(logging, AppConfig.LOG_LEVEL))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(AppConfig.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name=None):
    if name:
        return logging.getLogger(f"{AppConfig.APP_NAME}.{name}")
    return logging.getLogger(AppConfig.APP_NAME)
