import pandas as pd
from datetime import datetime
from app.utils.logger import logger
from config.settings import COL_FECHA, COL_CAMPAÑA, COLUMNAS_EMBUDO, POSTGRADO_KEYWORDS, PREGRADO_KEYWORDS

class ExcelProcessor:
    """Clase encargada del procesamiento de datos usando pandas."""
    
    def __init__(self):
        self.df = None

    def load_file(self, filepath):
        """Carga el archivo excel en un DataFrame."""
        try:
            logger.info(f"Cargando archivo: {filepath}")
            
            # Cargar archivo usando el motor super rápido 'calamine' y filtrando columnas desde el inicio
            required_cols = [COL_FECHA, COL_CAMPAÑA] + COLUMNAS_EMBUDO
            
            try:
                if filepath.lower().endswith('.csv'):
                    # Si es CSV, se lee nativamente (es muchísimo más rápido)
                    self.df = pd.read_csv(filepath, usecols=lambda c: c.strip() in required_cols, encoding='utf-8')
                else:
                    self.df = pd.read_excel(
                        filepath, 
                        engine="calamine",
                        usecols=lambda c: c.strip() in required_cols
                    )
            except Exception as e:
                # Si falla con usecols o codificación, intentar lectura completa o con otra codificación
                if filepath.lower().endswith('.csv'):
                    try:
                        self.df = pd.read_csv(filepath, encoding='utf-8')
                    except UnicodeDecodeError:
                        self.df = pd.read_csv(filepath, encoding='latin1')
                else:
                    self.df = pd.read_excel(filepath, engine="calamine")
                
            # Normalizar nombres de columnas (quitar espacios extra)
            self.df.columns = self.df.columns.str.strip()
            
            # Validar columnas requeridas
            missing = [col for col in required_cols if col not in self.df.columns]
            
            if missing:
                raise ValueError(f"Faltan las siguientes columnas requeridas: {', '.join(missing)}")
                
            # Convertir columna de fecha a datetime real (manejando errores)
            self.df[COL_FECHA] = pd.to_datetime(self.df[COL_FECHA], errors='coerce', dayfirst=True)
            
            # Remover filas con fechas inválidas o vacías si es necesario
            # self.df = self.df.dropna(subset=[COL_FECHA])
            
            # Calcular fechas min y max (ignorando nulos)
            min_date = self.df[COL_FECHA].min().date() if not self.df[COL_FECHA].isna().all() else None
            max_date = self.df[COL_FECHA].max().date() if not self.df[COL_FECHA].isna().all() else None
            
            logger.info(f"Archivo cargado exitosamente. {len(self.df)} registros encontrados.")
            return True, "Archivo cargado exitosamente.", min_date, max_date
        except Exception as e:
            logger.error(f"Error al cargar archivo: {str(e)}")
            return False, f"Error al cargar archivo: {str(e)}", None, None

    def process_data(self, start_date, end_date):
        """
        Filtra y agrupa los datos generando los dataframes necesarios.
        Retorna un diccionario de DataFrames listos para exportar.
        """
        if self.df is None or self.df.empty:
            raise ValueError("No hay datos cargados para procesar.")

        logger.info(f"Procesando datos desde {start_date} hasta {end_date}")
        
        # 1. Filtrar por fechas
        # Convertir start_date y end_date a Timestamp para una comparación segura con la serie datetime64
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(milliseconds=1)
        
        mask = (self.df[COL_FECHA] >= start_ts) & (self.df[COL_FECHA] <= end_ts)
        filtered_df = self.df.loc[mask].copy()
        
        if filtered_df.empty:
            logger.warning("No se encontraron registros en el rango de fechas seleccionado.")
            return {}

        # Mapear las categorías a partir de Nombre de Campaña
        filtered_df['SubCategoria_Postgrado'] = filtered_df[COL_CAMPAÑA].apply(lambda x: self._categorize(x, POSTGRADO_KEYWORDS))
        filtered_df['SubCategoria_Pregrado'] = filtered_df[COL_CAMPAÑA].apply(lambda x: self._categorize(x, PREGRADO_KEYWORDS))

        results = {}
        
        # 1. Generar consolidado Postgrado
        post_df = filtered_df[filtered_df['SubCategoria_Postgrado'].notna()].copy()
        results['Postgrado'] = self._generate_summary(post_df, 'SubCategoria_Postgrado', POSTGRADO_KEYWORDS)
            
        # 2. Generar consolidado Pregrado
        pre_df = filtered_df[filtered_df['SubCategoria_Pregrado'].notna()].copy()
        results['Pregrado'] = self._generate_summary(pre_df, 'SubCategoria_Pregrado', PREGRADO_KEYWORDS)
        
        # 3. Generar consolidado Otros / N/A
        otros_mask = filtered_df['SubCategoria_Postgrado'].isna() & filtered_df['SubCategoria_Pregrado'].isna()
        otros_df = filtered_df[otros_mask].copy()
        otros_df['SubCategoria_Otros'] = 'Sin Categoría'
        results['Otros'] = self._generate_summary(otros_df, 'SubCategoria_Otros', {'Sin Categoría': []})
                
        logger.info(f"Procesamiento completado. Se generaron {len(results)} cuadros.")
        return results

    def _categorize(self, campaign_name, keywords_dict):
        """Busca las palabras clave en el nombre de la campaña para clasificarla."""
        if pd.isna(campaign_name) or not str(campaign_name).strip():
            return None
        camp_name = str(campaign_name).upper()
        
        # Recorrer diccionario para ver a qué categoría pertenece
        for cat_name, keywords in keywords_dict.items():
            for kw in keywords:
                if kw.upper() in camp_name:
                    return cat_name
        return None

    def _generate_summary(self, df, group_col, keywords_dict):
        """
        Genera un resumen agrupando por la categoría detectada.
        Asegura que todas las subcategorías en keywords_dict aparezcan.
        """
        summary_data = {
            'Categoría': list(keywords_dict.keys()),
            'Generación': ["" for _ in keywords_dict]
        }
        for col in COLUMNAS_EMBUDO:
            summary_data[col] = ["" for _ in keywords_dict]
            
        pivot = pd.DataFrame(summary_data)
        pivot.set_index('Categoría', inplace=True)
        
        if not df.empty:
            grouped = df.groupby(group_col)
            for cat_val, group in grouped:
                if cat_val in pivot.index:
                    pivot.at[cat_val, 'Generación'] = len(group)
                    for col in COLUMNAS_EMBUDO:
                        count_exitosos = group[col].astype(str).str.strip().str.lower().isin(['exitosa', 'exitoso']).sum()
                        pivot.at[cat_val, col] = count_exitosos if count_exitosos > 0 else ""
                        
        pivot = pivot.reset_index()
        
        # Calcular totales usando pd.to_numeric para evitar warnings
        totals = {'Categoría': 'Todas las categorias'}
        gen_sum = pd.to_numeric(pivot['Generación'].replace("", 0)).sum()
        totals['Generación'] = gen_sum if gen_sum > 0 else ""
        
        for col in COLUMNAS_EMBUDO:
            sum_val = pd.to_numeric(pivot[col].replace("", 0)).sum()
            totals[col] = sum_val if sum_val > 0 else ""
            
        pivot.loc[len(pivot)] = totals
        
        return pivot
