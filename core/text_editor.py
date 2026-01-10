from PySide6.QtGui import QFont, QColor, QTextCharFormat, QCursor
from PySide6.QtWidgets import QFontDialog, QColorDialog

class TextEditorManager:
    """Gerencia o Requisito 14: Formatação de texto e biblioteca de fontes"""
    
    @staticmethod
    def format_selection(text_item, bold=None, italic=None, underline=None, color=None):
        """
        Aplica formatação. 
        Se houver seleção de cursor, aplica à seleção. 
        Caso contrário, aplica ao objeto todo.
        """
        cursor = text_item.textCursor()
        
        # Se não houver texto selecionado pelo cursor, selecionamos tudo
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.Document)
            
        fmt = QTextCharFormat()
        
        if bold is not None: 
            fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        if italic is not None: 
            fmt.setFontItalic(italic)
        if underline is not None: 
            fmt.setFontUnderline(underline)
        if color is not None: 
            fmt.setForeground(QColor(color))
            
        cursor.mergeCharFormat(fmt)
        text_item.setTextCursor(cursor)

    @staticmethod
    def open_font_dialog(parent, text_item):
        """Abre a biblioteca de fontes do Windows (Requisito 14)"""
        current_font = text_item.font()
        ok, font = QFontDialog.getFont(current_font, parent, "Escolha a Fonte")
        if ok:
            # Aplica a fonte escolhida ao item de texto
            text_item.setFont(font)