from PySide6.QtWidgets import QInputDialog

class IconManager:
    """Gerencia a inserção de emojis e ícones nos nós (Requisito 12)"""
    
    @staticmethod
    def open_emoji_picker(parent, item):
        emojis = ["📌", "💡", "🚀", "✅", "❌", "⚠️", "🔥", "⭐", "📅", "👤"]
        emoji, ok = QInputDialog.getItem(parent, "Inserir Ícone", "Escolha um símbolo:", emojis, 0, False)
        
        if ok and emoji:
            current_text = item.text_item.toPlainText()
            item.text_item.setPlainText(f"{emoji} {current_text}")