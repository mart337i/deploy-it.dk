import os
import logging

def setup_logging(app_name='app', log_filename='application.log', log_level=logging.INFO) -> logging.Logger:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(ROOT_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"Created logs directory at: {log_dir}")
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(os.path.join(log_dir, log_filename))
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    logging.basicConfig(level=log_level)
    
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(log_level)
    app_logger.addHandler(file_handler)

    app_logger.info(f"{app_name} logging system initialized")
    
    return app_logger


def set_log_level(logger_name='app', new_level=logging.INFO) -> bool:
    try:
        logger = logging.getLogger(logger_name)
        logger.setLevel(new_level)
        for handler in logger.handlers:
            handler.setLevel(new_level)
        return logger.level
    except Exception as e:
        return logger.level