import json
from PySide6.QtCore import QPointF, QRectF
from items.shapes import StyledNode, EllipseNode
from core.connection import SmartConnection

class PersistenceManager:
    def __init__(self, scene):
        self.scene = scene
        self.extension = ".amind"

    def save_to_file(self, file_path):
        """Varre a cena e salva todos os dados em formato JSON"""
        if not file_path.endswith(self.extension):
            file_path += self.extension

        data = {
            "nodes": [],
            "connections": []
        }

        # Separar itens para salvar na ordem correta
        for item in self.scene.items():
            if isinstance(item, StyledNode):
                node_data = {
                    "type": "rectangle" if not isinstance(item, EllipseNode) else "ellipse",
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "w": item.rect().width(),
                    "h": item.rect().height(),
                    "text": item.text_item.toPlainText(),
                    "id": id(item) # ID temporário para mapear conexões
                }
                data["nodes"].append(node_data)
            
            elif isinstance(item, SmartConnection):
                conn_data = {
                    "source_id": id(item.source),
                    "target_id": id(item.target),
                    "color": item.line_color.name(),
                    "label": item.label.toPlainText() if item.label else ""
                }
                data["connections"].append(conn_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_from_file(self, file_path):
        """Limpa a cena e reconstrói o mapa a partir do arquivo"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.scene.clear()
        node_map = {} # De-serialização de IDs

        # 1. Recriar os Nós
        for n in data["nodes"]:
            if n["type"] == "rectangle":
                node = StyledNode(n["x"], n["y"])
            else:
                node = EllipseNode(n["x"], n["y"])
            
            node.setRect(0, 0, n["w"], n["h"])
            node.text_item.setPlainText(n["text"])
            node.update_handle_positions()
            
            self.scene.addItem(node)
            node_map[n["id"]] = node

        # 2. Recriar as Conexões
        # Nota: Como as IDs mudam ao fechar o app, o carregamento de 
        # conexões entre sessões exige uma lógica de mapeamento espacial 
        # ou ID persistente. Para esta versão, reconstruímos a estrutura.
        for c in data["connections"]:
            src = node_map.get(c["source_id"])
            tgt = node_map.get(c["target_id"])
            if src and tgt:
                conn = SmartConnection(src, tgt)
                conn.change_color(c["color"])
                if c["label"]:
                    conn.set_label_text(c["label"])
                self.scene.addItem(conn)