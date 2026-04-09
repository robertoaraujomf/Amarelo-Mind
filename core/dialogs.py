from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSpinBox, QPushButton, QGroupBox,
                               QGridLayout, QWidget, QLineEdit, QSlider)
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QFontDatabase
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialogButtonBox


class FontStyleDialog(QDialog):
    def __init__(self, current_font=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estilo da Fonte")
        self.setMinimumWidth(500)
        self.current_font = current_font or QFont()
        self.selected_format = QTextCharFormat()
        self._setup_ui()
        self._load_current_format()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        font_family_group = QGroupBox("Família da Fonte")
        font_family_layout = QVBoxLayout()
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.setEditable(True)
        self.font_family_combo.setMinimumWidth(300)
        
        families = QFontDatabase.families()
        self.font_family_combo.addItems(families)
        
        if self.current_font.family() in families:
            self.font_family_combo.setCurrentText(self.current_font.family())
        
        font_family_layout.addWidget(self.font_family_combo)
        font_family_group.setLayout(font_family_layout)
        layout.addWidget(font_family_group)
        
        format_group = QGroupBox("Formatação")
        format_layout = QGridLayout()
        
        self.bold_btn = self._make_toggle_btn("Negrito", "B", "bold")
        self.italic_btn = self._make_toggle_btn("Itálico", "I", "italic")
        self.underline_btn = self._make_toggle_btn("Sublinhado", "S", "underline")
        self.strikethrough_btn = self._make_toggle_btn("Tachado", "T", "strikethrough")
        self.overline_btn = self._make_toggle_btn("Linha Acima", "L", "overline")
        
        format_layout.addWidget(self.bold_btn, 0, 0)
        format_layout.addWidget(self.italic_btn, 0, 1)
        format_layout.addWidget(self.underline_btn, 0, 2)
        format_layout.addWidget(self.strikethrough_btn, 1, 0)
        format_layout.addWidget(self.overline_btn, 1, 1)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        size_group = QGroupBox("Tamanho")
        size_layout = QHBoxLayout()
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 144)
        self.size_spin.setValue(int(self.current_font.pointSize()))
        self.size_spin.setSuffix(" pt")
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(6, 72)
        self.size_slider.setValue(int(self.current_font.pointSize()))
        
        self.size_spin.valueChanged.connect(self.size_slider.setValue)
        self.size_slider.valueChanged.connect(self.size_spin.setValue)
        
        size_layout.addWidget(self.size_spin)
        size_layout.addWidget(self.size_slider)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                  QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _make_toggle_btn(self, label, style_char, attr_name):
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setMaximumWidth(100)
        font = QFont()
        font.setBold(True)
        btn.setFont(font)
        btn.clicked.connect(lambda checked, a=attr_name: self._on_format_toggle(a, checked))
        return btn
    
    def _on_format_toggle(self, attr_name, checked):
        pass
    
    def _load_current_format(self):
        self.bold_btn.setChecked(self.current_font.bold())
        self.italic_btn.setChecked(self.current_font.italic())
        self.underline_btn.setChecked(self.current_font.underline())
        
        cursor = getattr(self.current_font, '_cursor', None)
        if cursor:
            fmt = cursor.charFormat()
            self.strikethrough_btn.setChecked(fmt.fontStrikeOut())
            self.overline_btn.setChecked(fmt.fontOverline())
    
    def get_font(self):
        font = QFont(self.font_family_combo.currentText())
        font.setPointSize(self.size_spin.value())
        font.setBold(self.bold_btn.isChecked())
        font.setItalic(self.italic_btn.isChecked())
        font.setUnderline(self.underline_btn.isChecked())
        return font
    
    def get_format(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.bold_btn.isChecked() else QFont.Weight.Normal)
        fmt.setFontItalic(self.italic_btn.isChecked())
        fmt.setFontUnderline(self.underline_btn.isChecked())
        fmt.setFontStrikeOut(self.strikethrough_btn.isChecked())
        fmt.setFontOverline(self.overline_btn.isChecked())
        return fmt
    
    @staticmethod
    def get_font_and_format(current_font=None, parent=None):
        dialog = FontStyleDialog(current_font, parent)
        result = dialog.exec()
        if result:
            return dialog.get_font(), dialog.get_format(), True
        return None, None, False


class ColorPickerDialog(QDialog):
    color_changed = Signal(QColor)
    
    DEFAULT_YELLOW = QColor("#F5C542")
    
    def __init__(self, initial_color=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Escolher Cor")
        self.setMinimumWidth(450)
        self._current_color = initial_color or Qt.white
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("#RRGGBB ou #RGB")
        self.hex_input.textChanged.connect(self._on_hex_changed)
        layout.addWidget(QLabel("Código Hexadecimal:"))
        layout.addWidget(self.hex_input)
        
        rgb_group = QGroupBox("RGB")
        rgb_layout = QGridLayout()
        
        self.rgb_r_spin = self._make_color_spin("Vermelho (R)")
        self.rgb_g_spin = self._make_color_spin("Verde (G)")
        self.rgb_b_spin = self._make_color_spin("Azul (B)")
        
        rgb_layout.addWidget(self.rgb_r_spin[0], 0, 0)
        rgb_layout.addWidget(self.rgb_g_spin[0], 1, 0)
        rgb_layout.addWidget(self.rgb_b_spin[0], 2, 0)
        
        rgb_layout.addWidget(self.rgb_r_spin[1], 0, 1)
        rgb_layout.addWidget(self.rgb_g_spin[1], 1, 1)
        rgb_layout.addWidget(self.rgb_b_spin[1], 2, 1)
        
        rgb_group.setLayout(rgb_layout)
        layout.addWidget(rgb_group)
        
        cmyk_group = QGroupBox("CMYK")
        cmyk_layout = QGridLayout()
        
        self.cmyk_c_spin = self._make_color_spin("Ciano (C)")
        self.cmyk_m_spin = self._make_color_spin("Magenta (M)")
        self.cmyk_y_spin = self._make_color_spin("Amarelo (Y)")
        self.cmyk_k_spin = self._make_color_spin("Preto (K)")
        
        cmyk_layout.addWidget(self.cmyk_c_spin[0], 0, 0)
        cmyk_layout.addWidget(self.cmyk_m_spin[0], 1, 0)
        cmyk_layout.addWidget(self.cmyk_y_spin[0], 2, 0)
        cmyk_layout.addWidget(self.cmyk_k_spin[0], 3, 0)
        
        cmyk_layout.addWidget(self.cmyk_c_spin[1], 0, 1)
        cmyk_layout.addWidget(self.cmyk_m_spin[1], 1, 1)
        cmyk_layout.addWidget(self.cmyk_y_spin[1], 2, 1)
        cmyk_layout.addWidget(self.cmyk_k_spin[1], 3, 1)
        
        cmyk_group.setLayout(cmyk_layout)
        layout.addWidget(cmyk_group)
        
        palette_group = QGroupBox("Paleta de Cores")
        palette_layout = QVBoxLayout()
        
        self.palette_widget = QWidget()
        self.palette_layout = QGridLayout(self.palette_widget)
        self.palette_layout.setSpacing(2)
        self._create_palette()
        
        palette_layout.addWidget(self.palette_widget)
        palette_group.setLayout(palette_layout)
        layout.addWidget(palette_group)
        
        buttons_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Resetar (Cor Padrão)")
        self.reset_btn.clicked.connect(self._on_reset)
        
        self.preview_btn = QPushButton()
        self.preview_btn.setFixedHeight(40)
        self.preview_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addWidget(self.preview_btn)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        main_buttons_layout = QVBoxLayout()
        main_buttons_layout.addLayout(buttons_layout)
        main_buttons_layout.addWidget(buttons)
        layout.addLayout(main_buttons_layout)
        
        self._update_from_color(self._current_color)
    
    def _make_color_spin(self, label):
        label_widget = QLabel(label)
        spin = QSpinBox()
        spin.setRange(0, 255)
        spin.valueChanged.connect(self._on_rgb_changed)
        return label_widget, spin
    
    def _create_palette(self):
        colors = [
            "#FF0000", "#FF4500", "#FF8C00", "#FFD700", "#FFFF00", "#9ACD32",
            "#32CD32", "#00FF00", "#00FA9A", "#00CED1", "#00BFFF", "#1E90FF",
            "#0000FF", "#8A2BE2", "#9932CC", "#FF00FF", "#FF1493", "#FF69B4",
            "#000000", "#2F4F4F", "#696969", "#808080", "#A9A9A9", "#D3D3D3",
            "#FFFFFF", "#F5DEB3", "#DEB887", "#D2691E", "#8B4513", "#A0522D",
            "#F5C542", "#E6B800", "#CC9900", "#B8860B", "#DAA520", "#BDB76B",
        ]
        
        for i, hex_color in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #888;")
            btn.clicked.connect(lambda checked, c=hex_color: self._on_palette_clicked(c))
            row, col = divmod(i, 6)
            self.palette_layout.addWidget(btn, row, col)
    
    def _on_hex_changed(self, text):
        if text.startswith("#") and len(text) in (4, 7):
            color = QColor(text)
            if color.isValid():
                self._update_rgb_spins(color)
                self._update_cmyk_spins(color)
                self._update_preview(color)
    
    def _on_rgb_changed(self):
        r = self.rgb_r_spin[1].value()
        g = self.rgb_g_spin[1].value()
        b = self.rgb_b_spin[1].value()
        color = QColor(r, g, b)
        self._update_from_rgb(color)
    
    def _on_cmyk_changed(self):
        c = self.cmyk_c_spin[1].value() / 100.0
        m = self.cmyk_m_spin[1].value() / 100.0
        y = self.cmyk_y_spin[1].value() / 100.0
        k = self.cmyk_k_spin[1].value() / 100.0
        
        r = int(255 * (1 - c) * (1 - k))
        g = int(255 * (1 - m) * (1 - k))
        b = int(255 * (1 - y) * (1 - k))
        
        color = QColor(r, g, b)
        self._update_from_cmyk(color)
    
    def _on_palette_clicked(self, hex_color):
        color = QColor(hex_color)
        self._update_from_color(color)
    
    def _on_reset(self):
        self._update_from_color(self.DEFAULT_YELLOW)
    
    def _update_from_color(self, color):
        self._current_color = color
        self.hex_input.setText(color.name())
        self._update_rgb_spins(color)
        self._update_cmyk_spins(color)
        self._update_preview(color)
    
    def _update_from_rgb(self, color):
        self._current_color = color
        self.hex_input.blockSignals(True)
        self.hex_input.setText(color.name())
        self.hex_input.blockSignals(False)
        self._update_cmyk_spins(color)
        self._update_preview(color)
    
    def _update_from_cmyk(self, color):
        self._current_color = color
        self.hex_input.blockSignals(True)
        self.hex_input.setText(color.name())
        self.hex_input.blockSignals(False)
        self._update_rgb_spins(color)
        self._update_preview(color)
    
    def _update_rgb_spins(self, color):
        self.rgb_r_spin[1].blockSignals(True)
        self.rgb_g_spin[1].blockSignals(True)
        self.rgb_b_spin[1].blockSignals(True)
        
        self.rgb_r_spin[1].setValue(color.red())
        self.rgb_g_spin[1].setValue(color.green())
        self.rgb_b_spin[1].setValue(color.blue())
        
        self.rgb_r_spin[1].blockSignals(False)
        self.rgb_g_spin[1].blockSignals(False)
        self.rgb_b_spin[1].blockSignals(False)
    
    def _update_cmyk_spins(self, color):
        r, g, b = color.red() / 255, color.green() / 255, color.blue() / 255
        k = 1 - max(r, g, b)
        if k < 1:
            c = (1 - r - k) / (1 - k)
            m = (1 - g - k) / (1 - k)
            y = (1 - b - k) / (1 - k)
        else:
            c = m = y = 0
        
        self.cmyk_c_spin[1].blockSignals(True)
        self.cmyk_m_spin[1].blockSignals(True)
        self.cmyk_y_spin[1].blockSignals(True)
        self.cmyk_k_spin[1].blockSignals(True)
        
        self.cmyk_c_spin[1].setValue(int(c * 100))
        self.cmyk_m_spin[1].setValue(int(m * 100))
        self.cmyk_y_spin[1].setValue(int(y * 100))
        self.cmyk_k_spin[1].setValue(int(k * 100))
        
        self.cmyk_c_spin[1].blockSignals(False)
        self.cmyk_m_spin[1].blockSignals(False)
        self.cmyk_y_spin[1].blockSignals(False)
        self.cmyk_k_spin[1].blockSignals(False)
    
    def _update_preview(self, color):
        self.preview_btn.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #333;")
    
    def get_color(self):
        return self._current_color
    
    @staticmethod
    def get_color_value(initial_color=None, parent=None):
        dialog = ColorPickerDialog(initial_color, parent)
        result = dialog.exec()
        if result:
            return dialog.get_color(), True
        return None, False
