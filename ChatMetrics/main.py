import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.controllers.main_controller import MainController
from app.utils.logger import logger

def main():
    logger.info("Iniciando aplicación ChatMetrics...")
    try:
        app = QApplication(sys.argv)
        
        # Forzar un estilo base limpio
        app.setStyle("Fusion")
        
        # Inicializar Controlador
        controller = MainController()
        
        # Inicializar Vista principal
        window = MainWindow(controller)
        window.show()
        
        logger.info("Aplicación iniciada correctamente.")
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Error fatal en la aplicación: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
