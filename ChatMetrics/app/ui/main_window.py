from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QDateEdit,
    QMessageBox, QFrame, QProgressBar,
    QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, QDate, QTimer, QPoint
from PySide6.QtGui import QPixmap
from datetime import datetime
import os
from app.utils.worker import WorkerThread
from app.utils.paths import resource_path
from config.settings import POSTGRADO_KEYWORDS, PREGRADO_KEYWORDS


class _CatDropdown(QFrame):
    """Popup flotante de subcategorías. Se cierra automáticamente al hacer clic fuera."""

    def __init__(self, toggle_btn):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)
        self.toggle_btn = toggle_btn
        self.just_hidden = False

    def hideEvent(self, event):
        super().hideEvent(event)
        self.toggle_btn.setChecked(False)
        self.just_hidden = True
        QTimer.singleShot(150, self._clear_flag)

    def _clear_flag(self):
        self.just_hidden = False


class MainWindow(QMainWindow):
    """Ventana Principal de ChatMetrics."""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._file_loaded = False
        self._cat_sections = {}   # {data_key: (parent_chk, [sub_chks])}
        self.setWindowTitle("ChatMetrics")
        self.setMinimumSize(660, 540)
        self.setup_ui()
        self.apply_styles()
        self._fit_to_screen()

    # ──────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ──────────────────────────────────────────────────────────────────

    def setup_ui(self):
        # Scroll area principal (robustez ante pantallas pequeñas)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("mainScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(scroll_area)

        content = QWidget()
        content.setObjectName("scrollContent")
        scroll_area.setWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(32, 18, 32, 24)
        main_layout.setSpacing(0)

        # ── HEADER ────────────────────────────────────────────────────
        title_label = QLabel("ChatMetrics")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Análisis de campañas de comunicación")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)

        sep = QFrame()
        sep.setObjectName("headerSeparator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(2)

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addSpacing(12)
        main_layout.addWidget(sep)
        main_layout.addSpacing(20)

        # ── ① SELECCIONAR ARCHIVO ────────────────────────────────────
        main_layout.addWidget(self._step_label("①  Seleccionar archivo"))
        main_layout.addSpacing(6)

        file_frame = QFrame()
        file_frame.setObjectName("sectionFrame")
        file_frame.setFrameShape(QFrame.StyledPanel)
        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(16, 12, 16, 12)
        file_layout.setSpacing(12)

        self.lbl_file_path = QLabel("Ningún archivo seleccionado")
        self.lbl_file_path.setObjectName("filePathLabel")

        self.btn_load_file = QPushButton("Seleccionar Excel")
        self.btn_load_file.setMinimumWidth(150)
        self.btn_load_file.clicked.connect(self.select_file)

        file_layout.addWidget(self.lbl_file_path, stretch=1)
        file_layout.addWidget(self.btn_load_file)

        main_layout.addWidget(file_frame)
        main_layout.addSpacing(18)

        # ── ② RANGO DE FECHAS ────────────────────────────────────────
        main_layout.addWidget(self._step_label("②  Rango de fechas"))
        main_layout.addSpacing(6)

        filter_frame = QFrame()
        filter_frame.setObjectName("sectionFrame")
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(10)

        self.date_start = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_start.setCalendarPopup(True)
        self.date_end = QDateEdit(QDate.currentDate())
        self.date_end.setCalendarPopup(True)

        lbl_desde = QLabel("Desde:")
        lbl_desde.setObjectName("fieldLabel")
        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setObjectName("fieldLabel")
        arrow = QLabel("→")
        arrow.setObjectName("arrowLabel")

        filter_layout.addWidget(lbl_desde)
        filter_layout.addWidget(self.date_start)
        filter_layout.addWidget(arrow)
        filter_layout.addWidget(lbl_hasta)
        filter_layout.addWidget(self.date_end)
        filter_layout.addStretch()

        main_layout.addWidget(filter_frame)
        main_layout.addSpacing(18)

        # ── ③ CATEGORÍAS (dropdowns flotantes) ──────────────────────────
        main_layout.addWidget(self._step_label("③  Categorías a exportar"))
        main_layout.addSpacing(6)

        cat_frame = QFrame()
        cat_frame.setObjectName("sectionFrame")
        cat_frame.setFrameShape(QFrame.StyledPanel)
        cat_outer = QVBoxLayout(cat_frame)
        cat_outer.setContentsMargins(16, 14, 16, 14)
        cat_outer.setSpacing(10)

        definitions = [
            ("Postgrado",   "Postgrado", list(POSTGRADO_KEYWORDS.keys())),
            ("Pregrado",    "Pregrado",  list(PREGRADO_KEYWORDS.keys())),
            ("Otros / N/A", "Otros",     ["Sin Categoría"]),
        ]

        # Los 3 botones al mismo nivel horizontal
        cats_row = QHBoxLayout()
        cats_row.setSpacing(10)
        self._cat_popups = {}

        for title, key, subs in definitions:
            btn = QPushButton(f"{title}  ▾")
            btn.setObjectName("catDropdownBtn")
            btn.setCheckable(True)
            cats_row.addWidget(btn, stretch=1)

            popup, parent_chk, sub_chks = self._make_cat_dropdown(btn, subs)
            self._cat_sections[key] = (parent_chk, sub_chks)
            self._cat_popups[key] = popup
            btn.clicked.connect(lambda _, b=btn, k=key: self._toggle_dropdown(b, k))

        cat_outer.addLayout(cats_row)

        apply_row = QHBoxLayout()
        apply_row.addStretch()
        self.btn_process = QPushButton("Aplicar Filtros")
        self.btn_process.setMinimumWidth(150)
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_data)
        apply_row.addWidget(self.btn_process)
        cat_outer.addLayout(apply_row)

        main_layout.addWidget(cat_frame)
        main_layout.addSpacing(20)

        # ── BARRA DE PROGRESO Y ESTADO ────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.setMinimumWidth(120)
        self.btn_cancel.clicked.connect(self.cancel_operation)
        self.btn_cancel.hide()

        pb_row = QHBoxLayout()
        pb_row.setSpacing(10)
        pb_row.addWidget(self.progress_bar, stretch=1)
        pb_row.addWidget(self.btn_cancel)
        main_layout.addLayout(pb_row)
        main_layout.addSpacing(6)

        self.lbl_status = QLabel("Listo. Por favor cargue un archivo.")
        self.lbl_status.setObjectName("statusLabel")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_status)

        # ── IMAGEN ANIMADA ────────────────────────────────────────────
        self.img_container = QWidget()
        img_layout = QHBoxLayout(self.img_container)
        img_layout.setAlignment(Qt.AlignCenter)
        img_layout.setContentsMargins(0, 4, 0, 4)

        self.img_wrapper = QWidget()
        self.img_wrapper.setFixedSize(160, 160)  # actualizado por _fit_to_screen

        self.chuwi_label = QLabel(self.img_wrapper)
        self.chuwi_label.setGeometry(0, 0, 160, 160)
        self.chuwi_label.setAlignment(Qt.AlignCenter)

        img_layout.addWidget(self.img_wrapper)
        main_layout.addWidget(self.img_container)

        self.sprite_timer = QTimer(self)
        self.sprite_timer.timeout.connect(self._update_sprite_frame)
        self.sprite_cols = 4
        self.sprite_rows = 2
        self.current_frame = 0

        img_path = resource_path("app/ui/ChuwiESAN.png")
        if os.path.exists(img_path):
            self.sprite_sheet = QPixmap(img_path)
            self._update_sprite_frame()

        main_layout.addStretch()

        # ── ④ EXPORTAR ────────────────────────────────────────────────
        main_layout.addWidget(self._step_label("④  Exportar resultados"))
        main_layout.addSpacing(6)

        self.btn_export = QPushButton("Exportar Resultados")
        self.btn_export.setObjectName("exportBtn")
        self.btn_export.setMinimumHeight(44)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_data)
        main_layout.addWidget(self.btn_export)

    # ──────────────────────────────────────────────────────────────────
    # HELPERS DE LAYOUT
    # ──────────────────────────────────────────────────────────────────

    def _fit_to_screen(self):
        """Ajusta el tamaño de la ventana y el Chuwi a la pantalla disponible."""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()

        w = min(880, max(660, int(screen.width()  * 0.78)))
        h = min(820, max(560, int(screen.height() * 0.93)))
        self.resize(w, h)

        # Chuwi ocupa el espacio sobrante (resto del layout fijo ≈ 610 px)
        chuwi_size = max(60, min(200, h - 610))
        self.img_wrapper.setFixedSize(chuwi_size, chuwi_size)
        self.chuwi_label.setGeometry(0, 0, chuwi_size, chuwi_size)
        self._update_sprite_frame()

        fg = self.frameGeometry()
        fg.moveCenter(screen.center())
        self.move(fg.topLeft())

    def _step_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("stepLabel")
        return lbl

    def _make_cat_dropdown(self, btn, sub_names):
        """Crea un popup flotante con checkboxes. Devuelve (popup, parent_chk, [sub_chks])."""
        popup = _CatDropdown(btn)
        popup.setObjectName("catDropdown")
        popup.setMinimumWidth(340)

        v = QVBoxLayout(popup)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(0)

        parent_chk = QCheckBox("Seleccionar todo")
        parent_chk.setObjectName("selectAllChk")
        parent_chk.setChecked(True)
        parent_chk.setTristate(True)
        v.addWidget(parent_chk)

        v.addSpacing(10)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("panelSep")
        v.addWidget(sep)
        v.addSpacing(12)

        sub_chks = []
        for sub in sub_names:
            chk = QCheckBox(sub)
            chk.setChecked(True)
            v.addWidget(chk)
            v.addSpacing(8)
            sub_chks.append(chk)

        def _parent_clicked(checked):
            for chk in sub_chks:
                chk.blockSignals(True)
                chk.setChecked(checked)
                chk.blockSignals(False)
            parent_chk.blockSignals(True)
            parent_chk.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            parent_chk.blockSignals(False)

        def _sub_changed():
            n = sum(1 for c in sub_chks if c.isChecked())
            parent_chk.blockSignals(True)
            if n == 0:
                parent_chk.setCheckState(Qt.Unchecked)
            elif n == len(sub_chks):
                parent_chk.setCheckState(Qt.Checked)
            else:
                parent_chk.setCheckState(Qt.PartiallyChecked)
            parent_chk.blockSignals(False)

        parent_chk.clicked.connect(_parent_clicked)
        for chk in sub_chks:
            chk.stateChanged.connect(_sub_changed)

        return popup, parent_chk, sub_chks

    def _toggle_dropdown(self, btn, cat_key):
        """Muestra u oculta el dropdown flotante de una categoría."""
        popup = self._cat_popups[cat_key]
        if popup.just_hidden:
            return
        if popup.isVisible():
            popup.hide()
            return
        pos = btn.mapToGlobal(QPoint(0, btn.height() + 4))
        popup.adjustSize()
        popup.move(pos)
        popup.show()
        popup.raise_()
        btn.setChecked(True)

    # ──────────────────────────────────────────────────────────────────
    # ESTILOS
    # ──────────────────────────────────────────────────────────────────

    def apply_styles(self):
        icon_path = resource_path("app/ui/calendar_icon.png")
        stylesheet = """
            * { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }

            QMainWindow, QWidget { background-color: #f5f5f7; }

            QScrollArea#mainScrollArea { background: transparent; border: none; }
            QWidget#scrollContent      { background-color: #f5f5f7; }

            /* Scrollbar principal (delgada, solo aparece al hacer scroll) */
            QScrollArea#mainScrollArea QScrollBar:vertical {
                background: #ebebed; width: 6px; border-radius: 3px; margin: 0;
            }
            QScrollArea#mainScrollArea QScrollBar::handle:vertical {
                background: #c0c0c5; border-radius: 3px; min-height: 28px;
            }
            QScrollArea#mainScrollArea QScrollBar::handle:vertical:hover {
                background: #a0a0a5;
            }
            QScrollArea#mainScrollArea QScrollBar::add-line:vertical,
            QScrollArea#mainScrollArea QScrollBar::sub-line:vertical { height: 0; }

            /* Botones de categoría (dropdown trigger) */
            QPushButton#catDropdownBtn {
                background-color: #f5f5f7;
                color: #3a3a3c;
                border: 1.5px solid #dcdde1;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton#catDropdownBtn:hover {
                background-color: #ececef;
                border-color: #c0c0c5;
            }
            QPushButton#catDropdownBtn:checked {
                background-color: #fce8ed;
                color: #e3173e;
                border-color: #e3173e;
            }

            /* Popup flotante de subcategorías */
            QFrame#catDropdown {
                background-color: #ffffff;
                border: 1.5px solid #dcdde1;
                border-radius: 10px;
            }
            QFrame#panelSep     { background-color: #ececec; border: none; max-height: 1px; }
            QCheckBox#selectAllChk { font-weight: bold; color: #231f20; }

            /* Labels generales */
            QLabel {
                color: #231f20; font-size: 13px;
                background: transparent; border: none;
            }
            QLabel#titleLabel {
                color: #e3173e; font-size: 26px; font-weight: bold;
                padding: 6px 0px 2px 0px; background: transparent;
            }
            QLabel#subtitleLabel {
                color: #8a8a8e; font-size: 12px;
                letter-spacing: 0.5px; background: transparent;
            }
            QFrame#headerSeparator {
                background-color: #e3173e; border: none; max-height: 2px;
            }
            QLabel#stepLabel {
                color: #58595b; font-size: 11px; font-weight: bold;
                letter-spacing: 1px; background: transparent;
            }
            QLabel#fieldLabel  { color: #58595b; font-size: 13px; background: transparent; }
            QLabel#arrowLabel  { color: #b0b0b5; font-size: 16px; background: transparent; }
            QLabel#statusLabel {
                color: #8a8a8e; font-size: 12px;
                font-style: italic; background: transparent;
            }
            QLabel#filePathLabel {
                color: #58595b; font-size: 13px;
                background-color: #ececec;
                border: 1px solid #dcdde1; border-radius: 5px;
                padding: 5px 10px; min-height: 20px;
            }

            /* Cards / secciones */
            QFrame#sectionFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e2e2e7;
            }

            /* Checkboxes */
            QCheckBox {
                font-size: 13px; color: #231f20;
                spacing: 8px; background: transparent;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 2px solid #dcdde1;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #e3173e;
                border-color: #e3173e;
            }
            QCheckBox::indicator:indeterminate {
                background-color: #f5a0b0;
                border-color: #e3173e;
            }
            QCheckBox::indicator:hover { border-color: #e3173e; }
            QCheckBox:disabled { color: #aeaeb2; }
            QCheckBox::indicator:disabled {
                background-color: #f0f0f0;
                border-color: #dcdde1;
            }

            /* Botones */
            QPushButton {
                background-color: #e3173e; color: white;
                border: none; padding: 9px 20px;
                border-radius: 7px; font-weight: bold;
                font-size: 13px; letter-spacing: 0.3px;
            }
            QPushButton:hover    { background-color: #cc1437; }
            QPushButton:pressed  { background-color: #a3102c; }
            QPushButton:disabled { background-color: #e8e8ed; color: #aeaeb2; border: none; }

            QPushButton#cancelBtn {
                background-color: #636366; padding: 9px 16px;
            }
            QPushButton#cancelBtn:hover   { background-color: #48484a; }
            QPushButton#cancelBtn:pressed { background-color: #231f20; }

            QPushButton#exportBtn {
                background-color: #e3173e; font-size: 14px;
                padding: 12px 24px; border-radius: 8px; letter-spacing: 0.5px;
            }
            QPushButton#exportBtn:hover    { background-color: #cc1437; }
            QPushButton#exportBtn:disabled { background-color: #e8e8ed; color: #aeaeb2; }

            /* Fechas */
            QDateEdit {
                padding: 6px 10px; min-width: 120px;
                border: 1px solid #dcdde1; border-radius: 6px;
                color: #231f20; background-color: #ffffff; font-size: 13px;
            }
            QDateEdit:focus { border: 1.5px solid #e3173e; }
            QDateEdit::drop-down {
                subcontrol-origin: padding; subcontrol-position: top right;
                width: 28px; border-left: 1px solid #dcdde1;
            }
            QDateEdit::down-arrow { image: url({icon_path}); width: 14px; height: 14px; }

            /* Barra de progreso */
            QProgressBar {
                border: none; border-radius: 3px;
                background-color: #e2e2e7; max-height: 6px;
            }
            QProgressBar::chunk { background-color: #e3173e; border-radius: 3px; }
        """
        resolved = stylesheet.replace("{icon_path}", icon_path)
        self.setStyleSheet(resolved)
        for popup in self._cat_popups.values():
            popup.setStyleSheet(resolved)

    # ──────────────────────────────────────────────────────────────────
    # ANIMACIÓN SPRITE
    # ──────────────────────────────────────────────────────────────────

    def _update_sprite_frame(self):
        if hasattr(self, 'sprite_sheet') and not self.sprite_sheet.isNull():
            fw = self.sprite_sheet.width() / self.sprite_cols
            fh = self.sprite_sheet.height() / self.sprite_rows
            col = self.current_frame % self.sprite_cols
            row = self.current_frame // self.sprite_cols
            pix = self.sprite_sheet.copy(int(col * fw), int(row * fh), int(fw), int(fh))
            sz = self.img_wrapper.width() or 160
            self.chuwi_label.setPixmap(
                pix.scaled(sz, sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.current_frame = (self.current_frame + 1) % (self.sprite_cols * self.sprite_rows)

    # ──────────────────────────────────────────────────────────────────
    # ESTADO DE CARGA
    # ──────────────────────────────────────────────────────────────────

    def _start_loading_ui(self, msg):
        self.lbl_status.setText(msg)
        self.lbl_status.setStyleSheet("color: #231f20; font-weight: bold; background: transparent;")
        self.progress_bar.setRange(0, 0)
        self.sprite_timer.start(120)
        self.btn_cancel.show()

    def _stop_loading_ui(self):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.sprite_timer.stop()
        self.current_frame = 0
        self._update_sprite_frame()
        self.btn_cancel.hide()

    def cancel_operation(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.cancel()
        self._stop_loading_ui()
        self.btn_load_file.setEnabled(True)
        self.btn_process.setEnabled(self._file_loaded)
        self.lbl_status.setText("Operación cancelada.")
        self.lbl_status.setStyleSheet("color: #58595b; font-style: italic;")

    # ──────────────────────────────────────────────────────────────────
    # SELECCIÓN DE CATEGORÍAS
    # ──────────────────────────────────────────────────────────────────

    def get_selected_categories(self):
        """Devuelve {cat_key: [sub_nombres]} con las selecciones activas."""
        selected = {}
        for cat_key, (_, sub_chks) in self._cat_sections.items():
            subs = [chk.text() for chk in sub_chks if chk.isChecked()]
            if subs:
                selected[cat_key] = subs
        return selected

    # ──────────────────────────────────────────────────────────────────
    # ACCIONES (lógica sin cambios)
    # ──────────────────────────────────────────────────────────────────

    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de datos", "", "Data Files (*.xlsx *.xls *.csv)"
        )
        if filepath:
            self.lbl_file_path.setText(filepath)
            self._start_loading_ui("Cargando archivo, por favor espere...")
            self.btn_load_file.setEnabled(False)
            self.worker = WorkerThread(self.controller.load_file, filepath)
            self.worker.finished.connect(self._on_file_loaded)
            self.worker.error.connect(lambda e: self.show_error("Error", str(e)))
            self.worker.start()

    def _on_file_loaded(self, result):
        self._stop_loading_ui()
        if len(result) == 4:
            success, msg, min_date, max_date = result
        else:
            success, msg = result[0], result[1]
            min_date = max_date = None

        self.btn_load_file.setEnabled(True)
        if success:
            self._file_loaded = True
            self.btn_process.setEnabled(True)
            self.btn_export.setEnabled(False)
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet("color: #231f20; font-weight: bold;")
            if min_date and max_date:
                self.date_start.setDate(QDate(min_date.year, min_date.month, min_date.day))
                self.date_end.setDate(QDate(max_date.year, max_date.month, max_date.day))
        else:
            self.btn_process.setEnabled(False)
            self.lbl_status.setText("Error al cargar.")
            self.lbl_status.setStyleSheet("color: #e3173e; font-weight: bold;")
            self.show_error("Error de Carga", msg)

    def process_data(self):
        start_date = self.date_start.date().toPython()
        end_date   = self.date_end.date().toPython()
        if start_date > end_date:
            self.show_error("Error", "La fecha de inicio no puede ser mayor que la fecha fin.")
            return
        self._start_loading_ui("Procesando datos...")
        self.btn_process.setEnabled(False)
        self.worker = WorkerThread(self.controller.process_data, start_date, end_date)
        self.worker.finished.connect(self._on_data_processed)
        self.worker.error.connect(lambda e: self.show_error("Error", str(e)))
        self.worker.start()

    def _on_data_processed(self, result):
        self._stop_loading_ui()
        success, msg = result
        self.btn_process.setEnabled(True)
        if success:
            self.btn_export.setEnabled(True)
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet("color: #231f20; font-weight: bold;")
            QMessageBox.information(self, "Éxito", "Procesamiento completado. Listo para exportar.")
        else:
            self.btn_export.setEnabled(False)
            self.lbl_status.setText("Error en el procesamiento.")
            self.lbl_status.setStyleSheet("color: #e3173e; font-weight: bold;")
            self.show_error("Error de Procesamiento", msg)

    def export_data(self):
        selected_categories = self.get_selected_categories()
        if not selected_categories:
            self.show_error("Sin categorías", "Seleccione al menos una categoría antes de exportar.")
            return
        default_name = f"Reporte_ChatMetrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte Como", default_name, "Excel Files (*.xlsx)"
        )
        if filepath:
            self._start_loading_ui("Exportando archivo, por favor espere...")
            self.btn_export.setEnabled(False)
            success, msg = self.controller.export_data(filepath, selected_categories)
            self._stop_loading_ui()
            self.btn_export.setEnabled(True)
            if success:
                self.lbl_status.setText(f"Exportación exitosa: {filepath}")
                self.lbl_status.setStyleSheet("color: #231f20; font-weight: bold;")
                QMessageBox.information(self, "Éxito", "El archivo fue exportado correctamente.")
            else:
                self.lbl_status.setText("Error al exportar.")
                self.lbl_status.setStyleSheet("color: #e3173e; font-weight: bold;")
                self.show_error("Error de Exportación", msg)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
