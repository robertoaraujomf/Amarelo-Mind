from PySide6.QtGui import QFont, QColor, QTextCharFormat, QCursor
from PySide6.QtWidgets import QFontDialog, QColorDialog

class TextEditorManager:
    """Gerencia o Requisito 14: Formatação de texto e biblioteca de fontes"""
    
    @staticmethod
    def format_selection(text_item, bold=None, italic=None, underline=None, 
                         strikethrough=None, overline=None, color=None):
        """
        Aplica formatação. 
        Se houver seleção de cursor, aplica à seleção. 
        Caso contrário, aplica ao objeto todo.
        """
        cursor = text_item.textCursor()
        
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.Document)
            
        fmt = QTextCharFormat()
        
        if bold is not None: 
            fmt.setFontWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        if italic is not None: 
            fmt.setFontItalic(italic)
        if underline is not None: 
            fmt.setFontUnderline(underline)
        if strikethrough is not None: 
            fmt.setFontStrikeOut(strikethrough)
        if overline is not None: 
            fmt.setFontOverline(overline)
        if color is not None: 
            fmt.setForeground(QColor(color))
            
        cursor.mergeCharFormat(fmt)
        text_item.setTextCursor(cursor)
    
    @staticmethod
    def toggle_format(text_item, format_type):
        """
        Alterna um formato específico no texto selecionado.
        
        Args:
            text_item: QGraphicsTextItem
            format_type: 'bold', 'italic', 'underline', 'strikethrough', 'overline'
        """
        cursor = text_item.textCursor()
        
        if not cursor.hasSelection():
            cursor.select(cursor.SelectionType.Document)
        
        current_fmt = cursor.charFormat()
        fmt = QTextCharFormat()
        
        if format_type == 'bold':
            current_weight = current_fmt.fontWeight()
            new_weight = QFont.Weight.Normal if current_weight >= QFont.Weight.Bold else QFont.Weight.Bold
            fmt.setFontWeight(new_weight)
        elif format_type == 'italic':
            fmt.setFontItalic(not current_fmt.fontItalic())
        elif format_type == 'underline':
            fmt.setFontUnderline(not current_fmt.fontUnderline())
        elif format_type == 'strikethrough':
            fmt.setFontStrikeOut(not current_fmt.fontStrikeOut())
        elif format_type == 'overline':
            fmt.setFontOverline(not current_fmt.fontOverline())
        
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