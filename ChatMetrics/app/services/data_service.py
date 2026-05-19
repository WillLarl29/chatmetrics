import pandas as pd
from app.processors.excel_processor import ExcelProcessor
from app.exporters.excel_exporter import ExcelExporter
from app.utils.logger import logger


class DataService:
    """Orquestador que coordina el procesamiento y la exportación."""

    def __init__(self):
        self.processor = ExcelProcessor()
        self.exporter = ExcelExporter()
        self.processed_data = None

    def load_file(self, filepath):
        """Carga el archivo usando el procesador."""
        return self.processor.load_file(filepath)

    def process_data(self, start_date, end_date):
        """Inicia el procesamiento de datos."""
        try:
            self.processed_data = self.processor.process_data(start_date, end_date)
            if not self.processed_data:
                return False, "No se encontraron datos en el rango seleccionado o el archivo está vacío."
            return True, "Datos procesados correctamente."
        except Exception as e:
            logger.error(f"Service Error en process_data: {str(e)}")
            return False, f"Error al procesar: {str(e)}"

    def export_data(self, output_path, selected_categories=None):
        """
        Exporta los datos procesados a Excel.
        selected_categories: dict {categoria: [subcategorias]} o None para exportar todo.
        """
        if not self.processed_data:
            return False, "No hay datos procesados para exportar."

        if selected_categories is None:
            return self.exporter.export(self.processed_data, output_path)

        filtered = {}
        for cat_key, df in self.processed_data.items():
            if cat_key not in selected_categories:
                continue

            selected_subs = selected_categories[cat_key]
            if not selected_subs:
                continue

            # Separar filas de datos de la fila de totales
            totals_mask = df['Categoría'].astype(str).str.startswith('Todas las')
            data_rows = df[~totals_mask & df['Categoría'].isin(selected_subs)].copy()

            if data_rows.empty:
                continue

            # Recalcular fila de totales con las subcategorías seleccionadas
            totals = {'Categoría': 'Todas las categorias'}
            for col in df.columns:
                if col == 'Categoría':
                    continue
                col_sum = pd.to_numeric(data_rows[col].replace("", 0), errors='coerce').sum()
                totals[col] = int(col_sum) if col_sum > 0 else ""

            filtered_df = pd.concat(
                [data_rows, pd.DataFrame([totals])], ignore_index=True
            )
            filtered[cat_key] = filtered_df

        return self.exporter.export(filtered, output_path)
