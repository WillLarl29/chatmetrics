from app.services.data_service import DataService
from app.utils.logger import logger

class MainController:
    """Controlador que intermedia entre la vista (UI) y la capa de servicios."""
    
    def __init__(self):
        self.service = DataService()

    def load_file(self, filepath):
        """Pide al servicio que cargue el archivo."""
        logger.info("Controller: Solicitud de carga de archivo iniciada.")
        return self.service.load_file(filepath)

    def process_data(self, start_date, end_date):
        """Pide al servicio que procese los datos en el rango dado."""
        logger.info(f"Controller: Solicitud de procesamiento de datos ({start_date} a {end_date}).")
        return self.service.process_data(start_date, end_date)

    def export_data(self, output_path, selected_categories=None):
        """Pide al servicio que exporte los resultados procesados."""
        logger.info(f"Controller: Solicitud de exportación a {output_path}. Categorías: {selected_categories}.")
        return self.service.export_data(output_path, selected_categories)
