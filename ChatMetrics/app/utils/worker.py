from PySide6.QtCore import QThread, Signal

class WorkerThread(QThread):
    """
    Hilo de trabajo genérico para ejecutar funciones bloqueantes en segundo plano
    y mantener la interfaz gráfica (UI) responsiva.
    """
    finished = Signal(object) # Emite el resultado cuando termina
    error = Signal(str)       # Emite el error si ocurre una excepción
    cancelled = Signal()      # Emite cuando la operación fue cancelada

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            if not self.isInterruptionRequested():
                self.finished.emit(result)
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error.emit(str(e))

    def cancel(self):
        self.requestInterruption()
        self.terminate()
        self.cancelled.emit()
