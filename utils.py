import logging

def log_and_print(msg, logger_level):
    if logger_level != 'error':
        print(msg)
    
    if logger_level == 'info':
        logging.info(msg)
    elif logger_level == 'debug':
        logging.debug(msg)
    elif logger_level == 'warning':
        logging.warning(msg)
    elif logger_level == 'error':
        logging.error(msg)
    elif logger_level == 'critical':
        logging.critical(msg)
    else:
        raise ValueError(f"Invalid logger level: {logger_level}")