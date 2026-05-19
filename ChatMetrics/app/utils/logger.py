# app/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
import os
from config.settings import LOG_DIR

def setup_logger():
    """Configura y retorna el logger principal de la aplicación."""
    logger = logging.getLogger("ChatMetrics")
    
    # Evitar configurar múltiples veces
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Formato de los logs
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Handler para archivo
        log_file = os.path.join(LOG_DIR, "app.log")
        # Rotación de logs: Máximo 5MB (5 * 1024 * 1024 bytes), mantiene 3 backups (app.log.1, app.log.2...)
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger

logger = setup_logger()
