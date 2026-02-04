import json
import os
from typing import Dict, List, Any
from PySide6.QtGui import QColor

class PersistenceManager:
    """Gerencia salvamento e carregamento de projetos Amarelo Mind"""
    
    FILE_EXTENSION = ".amind"
    FILE_VERSION = "1.0"
    
    def __init__(self, scene=None):
        self.scene = scene
        self.nodes_map = {}  # Mapeia IDs de objetos para referência
    
    def _update_font_from_html(self, node, html):
        """Extrai informações de fonte do HTML e aplica ao widget"""
        import re
        
        # Procurar por informações de fonte no estilo do body
        body_style_match = re.search(r'<body[^>]*style="[^"]*font-family:([^;]+);[^"]*font-size:(\d+)pt', html)
        if body_style_match:
            family = body_style_match.group(1).strip('\'"')
            size = int(body_style_match.group(2))
            
            # Aplicar ao widget
            current_font = node.text.font()
            current_font.setFamily(family)
            current_font.setPointSize(size)
            node.text.setFont(current_font)
    
    def save_to_file(self, file_path: str, scene) -> bool:
        """
        Varre a cena e salva todos os dados em formato JSON
        
        Args:
            file_path: Caminho do arquivo para salvar
            scene: Cena a ser salva
        
        Returns:
            bool: True se salvo com sucesso
        """
        try:
            from items.shapes import StyledNode
            from core.connection import SmartConnection
            
            if not file_path.endswith(self.FILE_EXTENSION):
                file_path += self.FILE_EXTENSION
            
            data = {
                "version": self.FILE_VERSION,
                "nodes": [],
                "connections": []
            }
            
            nodes_by_id = {}
            
            # Separar itens para salvar na ordem correta
            for item in scene.items():
                if isinstance(item, StyledNode):
                    node_id = id(item)
                    node_data = {
                        "id": node_id,
                        "x": item.pos().x(),
                        "y": item.pos().y(),
                        "w": item.rect().width(),
                        "h": item.rect().height(),
                        "text": item.get_text(),
                        "html": item.text.document().toHtml(),  # Salvar HTML completo com formatação
                        "type": item.node_type,
                        "shadow": item.has_shadow,
                        "custom_color": item.custom_color
                    }
                    data["nodes"].append(node_data)
                    nodes_by_id[node_id] = node_data
                
                elif isinstance(item, SmartConnection):
                    try:
                        conn_data = {
                            "source_id": id(item.source),
                            "target_id": id(item.target)
                        }
                        data["connections"].append(conn_data)
                    except:
                        pass  # Ignora conexões órfãs
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Erro ao salvar projeto: {e}")
            return False
    
    def load_from_file(self, file_path: str, scene, window=None) -> bool:
        """
        Limpa a cena e reconstrói o mapa a partir do arquivo
        
        Args:
            file_path: Caminho do arquivo para carregar
            scene: Cena onde adicionar os objetos
            window: Janela principal (opcional) para conectar sinais
        
        Returns:
            bool: True se carregado com sucesso
        """
        try:
            from items.shapes import StyledNode
            from core.connection import SmartConnection
            
            if not os.path.exists(file_path):
                print(f"Arquivo não encontrado: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            scene.clear()
            self.nodes_map = {}
            
            # Reconstruir nós primeiro
            for node_data in data.get("nodes", []):
                node = StyledNode(
                    node_data["x"],
                    node_data["y"],
                    int(node_data.get("w", 200)),
                    int(node_data.get("h", 100)),
                    node_data.get("type", "Normal")
                )
                # Usar HTML se disponível para preservar formatação
                html_content = node_data.get("html")
                if html_content:
                    node.text.setHtml(html_content)
                    # Forçar atualização da fonte do widget baseada no HTML
                    self._update_font_from_html(node, html_content)
                else:
                    node.set_text(node_data.get("text", ""))
                node.update_color()
                
                custom_color = node_data.get("custom_color")
                if custom_color:
                    node.set_background(QColor(custom_color))
                
                if not node_data.get("shadow", True):
                    node.toggle_shadow()
                scene.addItem(node)
                self.nodes_map[node_data["id"]] = node
                
                # Conectar sinais de seleção de texto se houver janela
                if window and hasattr(node.text, 'selectionChanged'):
                    node.text.selectionChanged.connect(window.update_button_states)
            
            # Reconstruir conexões
            for conn_data in data.get("connections", []):
                source_id = conn_data.get("source_id")
                target_id = conn_data.get("target_id")
                
                if source_id in self.nodes_map and target_id in self.nodes_map:
                    source = self.nodes_map[source_id]
                    target = self.nodes_map[target_id]
                    connection = SmartConnection(source, target)
                    scene.addItem(connection)
            
            return True
        except Exception as e:
            print(f"Erro ao carregar projeto: {e}")
            return False
