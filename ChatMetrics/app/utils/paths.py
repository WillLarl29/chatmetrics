import os
import sys


def resource_path(relative_path):
    """Ruta a un recurso estático (imágenes, íconos). Compatible con PyInstaller."""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, relative_path).replace("\\", "/")


def writable_path(relative_path):
    """Ruta a un directorio de escritura (logs, exports). Se ubica junto al ejecutable."""
    if hasattr(sys, '_MEIPASS'):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, relative_path)