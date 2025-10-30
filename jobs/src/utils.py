from prefect import context

def log(msg):
    """Log usando o logger do Prefect"""
    logger = context.get("logger")
    if logger:
        logger.info(msg)


