"""
Filtro e seleção de registros/itens
"""
from typing import List, Callable
from items.shapes import StyledNode


class ItemFilter:
    """Filtro para seleção de itens da cena"""
    
    def __init__(self, scene):
        self.scene = scene
        self.filters = []
    
    def add_filter(self, filter_func: Callable[[StyledNode], bool]):
        """Adiciona um filtro à lista"""
        self.filters.append(filter_func)
    
    def clear_filters(self):
        """Remove todos os filtros"""
        self.filters = []
    
    def get_filtered_items(self) -> List[StyledNode]:
        """Retorna itens que passam em todos os filtros"""
        items = [item for item in self.scene.items() if isinstance(item, StyledNode)]
        
        for filter_func in self.filters:
            items = [item for item in items if filter_func(item)]
        
        return items
    
    def select_filtered_items(self):
        """Seleciona itens que passam nos filtros"""
        self.scene.clearSelection()
        for item in self.get_filtered_items():
            item.setSelected(True)
    
    # Filtros predefinidos
    def filter_by_type(self, node_type: str) -> List[StyledNode]:
        """Filtra por tipo de nó"""
        return [item for item in self.scene.items() 
                if isinstance(item, StyledNode) and item.node_type == node_type]
    
    def filter_by_text(self, search_text: str) -> List[StyledNode]:
        """Filtra por texto contido no nó"""
        search_text = search_text.lower()
        return [item for item in self.scene.items() 
                if isinstance(item, StyledNode) and search_text in item.get_text().lower()]
    
    def filter_by_position(self, x_min: float, y_min: float, x_max: float, y_max: float) -> List[StyledNode]:
        """Filtra por posição/região"""
        return [item for item in self.scene.items() 
                if isinstance(item, StyledNode) 
                and x_min <= item.pos().x() <= x_max 
                and y_min <= item.pos().y() <= y_max]
    
    def filter_with_shadow(self) -> List[StyledNode]:
        """Filtra itens com sombra"""
        return [item for item in self.scene.items() 
                if isinstance(item, StyledNode) and item.has_shadow]
    
    def select_by_type(self, node_type: str):
        """Seleciona todos os itens de um tipo específico"""
        self.scene.clearSelection()
        for item in self.filter_by_type(node_type):
            item.setSelected(True)
    
    def select_by_text(self, search_text: str):
        """Seleciona todos os itens que contêm o texto"""
        self.scene.clearSelection()
        for item in self.filter_by_text(search_text):
            item.setSelected(True)
    
    def get_statistics(self) -> dict:
        """Retorna estatísticas sobre os itens da cena"""
        items = [item for item in self.scene.items() if isinstance(item, StyledNode)]
        
        type_counts = {}
        for item in items:
            type_counts[item.node_type] = type_counts.get(item.node_type, 0) + 1
        
        shadow_count = len([item for item in items if item.has_shadow])
        
        return {
            "total_items": len(items),
            "type_breakdown": type_counts,
            "items_with_shadow": shadow_count,
            "items_without_shadow": len(items) - shadow_count
        }
