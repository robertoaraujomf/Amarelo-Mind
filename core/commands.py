from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF

class MoveCommand(QUndoCommand):
    """Comando para desfazer/refazer movimento de objetos"""
    def __init__(self, item, old_pos, new_pos):
        super().__init__("Mover Objeto")
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def undo(self):
        self.item.setPos(self.old_pos)

    def redo(self):
        self.item.setPos(self.new_pos)

class AddNodeCommand(QUndoCommand):
    """Comando para desfazer/refazer criação de objetos"""
    def __init__(self, scene, node):
        super().__init__("Adicionar Objeto")
        self.scene = scene
        self.node = node

    def undo(self):
        self.scene.removeItem(self.node)

    def redo(self):
        self.scene.addItem(self.node)