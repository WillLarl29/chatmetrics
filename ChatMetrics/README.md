# ChatMetrics Analytics

Software de escritorio para el procesamiento y análisis de datos de campañas de WhatsApp.

## Características
- Carga de archivos Excel con datos en crudo.
- Filtrado por rango de fechas ("Fecha del mensaje").
- Clasificación por categorías (Postgrado, Pregrado, etc.).
- Sumarización del embudo de conversión (Generación, Salida, Envío, Entrega, Lectura, Respuesta).
- Exportación profesional a Excel con hojas separadas y estilos corporativos.

## Requisitos Previos
- Python 3.9 o superior.
- Crear un entorno virtual (recomendado).

## Instalación

1. Clona o copia esta carpeta a tu entorno de trabajo.
2. Crea y activa un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Mac/Linux:
   source venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución (Desarrollo)
```bash
python main.py
```

## Compilación (Generar .exe)
Para distribuir la aplicación sin necesidad de instalar Python en la máquina destino, puedes generar un ejecutable usando PyInstaller.
Abre tu terminal en esta carpeta (`ChatMetrics`) y ejecuta:

```bash
pyinstaller --noconfirm --onedir --windowed --name "ChatMetrics" main.py
```

- `--noconfirm`: Sobrescribe carpetas de compilación anteriores sin preguntar.
- `--onedir`: Crea una carpeta con el `.exe` y sus dependencias (recomendado sobre `--onefile` para apps grandes ya que carga más rápido).
- `--windowed`: Evita que se abra una consola negra detrás de la interfaz gráfica.

Una vez finalizado, encontrarás la aplicación lista para usar dentro de la carpeta `dist/ChatMetrics/`.
Solo necesitas comprimir esa carpeta en `.zip` y enviarla a los usuarios.

## Configuraciones
Puedes editar el archivo `config/settings.py` si en el futuro cambian los nombres de las columnas del reporte original o los estados del embudo.
