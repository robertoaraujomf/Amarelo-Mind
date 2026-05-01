"""
Módulo de posicionamento inteligente de nós e conexões.
Fornece algoritmos de busca radial para posicionamento e verificação de interseção para conexões.
"""
import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QGraphicsPathItem


def find_best_position_radial(source, scene, node_width=200, node_height=100, min_distance=30, max_distance=500, collision_margin=15):
    """
    Encontra a melhor posição para um novo nó usando busca radial.
    
    Regras de validação:
        1. Hard Constraint: Posição não pode sobrepor objetos nem linhas de conexão existentes
        2. Soft Constraint: Prioriza posições com menor número de cruzamentos de linhas
    
    Args:
        source: O nó fonte (objeto existente selecionado)
        scene: A cena do PyQt onde os objetos estão
        node_width: Largura do novo nó
        node_height: Altura do novo nó
        min_distance: Distância mínima do nó fonte
        max_distance: Distância máxima de busca
        collision_margin: Margem de segurança para detecção de colisão
    
    Returns:
        QPointF: Posição (x, y) do canto superior esquerdo do novo nó
    """
    source_rect = source.sceneBoundingRect()
    source_center = source_rect.center()
    
    all_items = list(scene.items())
    
    def get_connection_lines():
        """Retorna todas as linhas de conexão (QGraphicsPathItem)."""
        return [item for item in all_items if isinstance(item, QGraphicsPathItem)]
    
    def has_hard_collision(pos, width, height):
        """Verifica colisão com objetos e linhas de conexão (Hard Constraint)."""
        new_rect = QRectF(pos.x(), pos.y(), width, height)
        expanded_rect = new_rect.adjusted(-collision_margin, -collision_margin, collision_margin, collision_margin)
        
        for item in all_items:
            if item == source:
                continue
            if not hasattr(item, 'sceneBoundingRect'):
                continue
            if isinstance(item, QGraphicsPathItem):
                continue
            
            item_rect = item.sceneBoundingRect()
            if expanded_rect.intersects(item_rect):
                return True
        
        node_rect = QRectF(pos.x(), pos.y(), width, height)
        for conn_line in get_connection_lines():
            if _rect_intersects_path(node_rect, conn_line.path()):
                return True
        
        return False
    
    def count_line_crossings(pos, width, height):
        """Conta quantas linhas de conexão a conexão do novo nó cruzaria (Soft Constraint)."""
        node_center = QPointF(pos.x() + width / 2, pos.y() + height / 2)
        crossings = 0
        
        for conn_line in get_connection_lines():
            if _line_segments_intersect(source_center, node_center, conn_line.path()):
                crossings += 1
        
        return crossings
    
    valid_positions = []
    
    num_angles = 36
    distance_step = 20
    
    for angle_idx in range(num_angles):
        angle = 2 * math.pi * angle_idx / num_angles
        
        for dist in range(int(min_distance), int(max_distance), distance_step):
            x = source_center.x() + math.cos(angle) * dist - node_width / 2
            y = source_center.y() + math.sin(angle) * dist - node_height / 2
            candidate_pos = QPointF(x, y)
            
            if not has_hard_collision(candidate_pos, node_width, node_height):
                crossings = count_line_crossings(candidate_pos, node_width, node_height)
                valid_positions.append((candidate_pos, dist, crossings))
                break
    
    if not valid_positions:
        fallback_dist = min_distance + 50
        fallback_x = source_center.x() + fallback_dist - node_width / 2
        fallback_y = source_center.y() - node_height / 2
        return QPointF(fallback_x, fallback_y)
    
    valid_positions.sort(key=lambda p: (p[2], p[1]))
    
    return valid_positions[0][0]


def _rect_intersects_path(rect, path):
    """Verifica se um retângulo intersecta um caminho (path)."""
    if path.elementCount() < 2:
        return False
    
    bounding = path.boundingRect()
    if not rect.intersects(bounding):
        return False
    
    for i in range(path.elementCount() - 1):
        p1 = path.elementAt(i)
        p2 = path.elementAt(i + 1)
        line_start = QPointF(p1.x, p1.y)
        line_end = QPointF(p2.x, p2.y)
        
        if _line_intersects_rect(line_start, line_end, rect):
            return True
        
        if rect.contains(line_start) or rect.contains(line_end):
            return True
    
    return False


def _line_segments_intersect(p1, p2, path):
    """Verifica se uma linha (p1-p2) intersecta algum segmento de um path."""
    if path.elementCount() < 2:
        return False
    
    for i in range(path.elementCount() - 1):
        ep1 = path.elementAt(i)
        ep2 = path.elementAt(i + 1)
        line_a = QPointF(ep1.x, ep1.y)
        line_b = QPointF(ep2.x, ep2.y)
        
        if _segments_intersect(p1, p2, line_a, line_b):
            return True
    
    return False


def check_connection_intersection(source, target, scene, exclude_connection=None):
    """
    Verifica se a linha de conexão direta entre dois nós intersecta outros elementos.
    
    Args:
        source: Nó de origem
        target: Nó de destino
        scene: A cena do PyQt
        exclude_connection: Conexão a excluir da verificação (opcional)
    
    Returns:
        tuple: (has_intersection, intersecting_items, connection_lines)
    """
    source_rect = source.sceneBoundingRect()
    target_rect = target.sceneBoundingRect()
    
    start = source_rect.center()
    end = target_rect.center()
    
    intersecting_items = []
    connection_lines = []
    
    search_rect = QRectF(
        min(start.x(), end.x()) - 50,
        min(start.y(), end.y()) - 50,
        abs(end.x() - start.x()) + 100,
        abs(end.y() - start.y()) + 100
    )
    
    for item in scene.items(search_rect):
        if item == source or item == target:
            continue
        if item == exclude_connection:
            continue
            
        if isinstance(item, QGraphicsPathItem):
            path = item.path()
            if path.elementCount() > 0:
                connection_lines.append(item)
                continue
        
        if hasattr(item, 'sceneBoundingRect') and not isinstance(item, QGraphicsPathItem):
            item_rect = item.sceneBoundingRect().adjusted(-10, -10, 10, 10)
            if _line_intersects_rect(start, end, item_rect):
                intersecting_items.append(item)
    
    has_intersection = len(intersecting_items) > 0 or len(connection_lines) > 0
    
    return has_intersection, intersecting_items, connection_lines


def _line_intersects_rect(start, end, rect):
    """Verifica se uma linha intersecta um retângulo."""
    if rect.contains(start) or rect.contains(end):
        return False
    
    lines = [
        (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
        (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
        (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
        (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top()))
    ]
    
    for p1, p2 in lines:
        if _segments_intersect(start, end, p1, p2):
            return True
    
    return False


def _segments_intersect(a1, a2, b1, b2):
    """Verifica se dois segmentos de linha se intersectam."""
    def ccw(A, B, C):
        return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())
    
    return ccw(a1, b1, b2) != ccw(a2, b1, b2) and ccw(a1, a2, b1) != ccw(a1, a2, b2)


def calculate_optimal_anchor_points(source_rect, target_rect, prefer_horizontal=True):
    """
    Calcula os melhores pontos de ancoragem nas bordas dos objetos para minimizar cruzamentos.
    
    Args:
        source_rect: QRectF do objeto fonte
        target_rect: QRectF do objeto alvo
        prefer_horizontal: Preferir conexão horizontal vs vertical
    
    Returns:
        tuple: (source_anchor, target_anchor) - dois QPointF
    """
    sc = source_rect.center()
    tc = target_rect.center()
    
    dx = tc.x() - sc.x()
    dy = tc.y() - sc.y()
    
    if abs(dx) > abs(dy):
        if dx > 0:
            source_anchor = QPointF(source_rect.right(), sc.y())
            target_anchor = QPointF(target_rect.left(), tc.y())
        else:
            source_anchor = QPointF(source_rect.left(), sc.y())
            target_anchor = QPointF(target_rect.right(), tc.y())
    else:
        if dy > 0:
            source_anchor = QPointF(sc.x(), source_rect.bottom())
            target_anchor = QPointF(tc.x(), target_rect.top())
        else:
            source_anchor = QPointF(sc.x(), source_rect.top())
            target_anchor = QPointF(tc.x(), target_rect.bottom())
    
    return source_anchor, target_anchor


def find_optimal_connection_path(source, target, scene, exclude_connection=None):
    """
    Encontra o caminho ideal para a conexão entre dois nós, considerando:
    1. Pontos de ancoragem ótimos nas bordas
    2. Verificação de interseção com outros elementos
    3. Desvio de obstáculos se necessário
    
    Args:
        source: Nó de origem
        target: Nó de destino
        scene: A cena do PyQt
        exclude_connection: Conexão a excluir
    
    Returns:
        tuple: (start_point, end_point, path_points)
    """
    source_rect = source.sceneBoundingRect()
    target_rect = target.sceneBoundingRect()
    
    source_anchor, target_anchor = calculate_optimal_anchor_points(source_rect, target_rect)
    
    has_intersection, obstacles, _ = check_connection_intersection(
        source, target, scene, exclude_connection
    )
    
    if not has_intersection:
        return source_anchor, target_anchor, [source_anchor, target_anchor]
    
    path_points = [source_anchor]
    
    for obstacle in obstacles:
        obs_rect = obstacle.sceneBoundingRect()
        mid_x = (source_anchor.x() + target_anchor.x()) / 2
        mid_y = (source_anchor.y() + target_anchor.y()) / 2
        
        if obs_rect.left() < mid_x < obs_rect.right():
            if source_anchor.y() < target_anchor.y():
                detour = QPointF(mid_x, obs_rect.bottom() + 20)
            else:
                detour = QPointF(mid_x, obs_rect.top() - 20)
        else:
            if source_anchor.x() < target_anchor.x():
                detour = QPointF(obs_rect.right() + 20, mid_y)
            else:
                detour = QPointF(obs_rect.left() - 20, mid_y)
        
        path_points.append(detour)
    
    path_points.append(target_anchor)
    
    return source_anchor, target_anchor, path_points