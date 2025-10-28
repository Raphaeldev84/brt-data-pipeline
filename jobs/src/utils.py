from prefect import context
from datetime import datetime

def log(msg):
    """Log que funciona dentro e fora de contexto Prefect"""
    try:
        logger = context.get("logger")
        if logger:
            logger.info(msg)
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    except Exception:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


