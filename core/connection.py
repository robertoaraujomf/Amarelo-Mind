from PySide6.QtWidgets import QGraphicsPathItem, QStyle, QGraphicsRectItem
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainter
import heapq
import math
import numpy as np
try:
    from shapely.geometry import LineString, Polygon, Point, box
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    
try:
    from scipy.interpolate import splprep, splev
    from scipy.interpolate import BSpline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

class SmartConnection(QGraphicsPathItem):
    """Conexão curva ou reta entre objetos"""
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        # Azul conforme solicitado para o ícone de conexão
        self.setPen(QPen(QColor("#0078d4"), 3, Qt.SolidLine, Qt.RoundCap))
        self.setZValue(-1) # Garante que a linha fique por baixo dos nós
        
        # Tornar a conexão selecionável
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        self.update_path()

    def update_path(self):
        """Atualiza o caminho com sistema otimizado de roteamento"""
        if not self.source.scene() or not self.target.scene():
            return

        start = self.source.sceneBoundingRect().center()
        end = self.target.sceneBoundingRect().center()
        
        # Verificar se as coordenadas são válidas
        if not (self._is_valid_point(start) and self._is_valid_point(end)):
            return
        
        # Verificar distância máxima (evitar linhas infinitas)
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 10000:  # Limite de 10000 pixels
            return
        
        # Usar sistema simplificado e rápido
        self._update_path_fast(start, end)
    
    def _is_valid_point(self, point):
        """Verifica se um ponto tem coordenadas válidas"""
        import math
        return (isinstance(point.x(), (int, float)) and 
                isinstance(point.y(), (int, float)) and
                not math.isnan(point.x()) and 
                not math.isnan(point.y()) and
                not math.isinf(point.x()) and 
                not math.isinf(point.y()))

    def _update_path_fast(self, start, end):
        """Sistema rápido de roteamento ortogonal com desvio de obstáculos"""
        # Verificar se há obstáculos no caminho direto
        obstacles = self._get_obstacles_between(start, end)
        
        if not obstacles:
            # Sem obstáculos - linha direta suave
            self._create_smooth_connection(start, end)
        else:
            # Com obstáculos - rota ortogonal contornando
            self._create_orthogonal_route(start, end, obstacles)

    def _get_obstacles_between(self, start, end):
        """Obtém obstáculos no caminho entre dois pontos (versão rápida)"""
        if not self.source.scene():
            return []
        
        # Importar aqui para evitar circular imports
        from items.shapes import StyledNode
        from items.base_node import MindMapNode
        
        obstacles = []
        # Área de busca expandida
        margin = 20
        search_rect = QRectF(
            min(start.x(), end.x()) - margin,
            min(start.y(), end.y()) - margin,
            abs(end.x() - start.x()) + margin * 2,
            abs(end.y() - start.y()) + margin * 2
        )
        
        for item in self.source.scene().items(search_rect):
            if item in (self, self.source, self.target):
                continue
            # Só considerar nós principais como obstáculos (StyledNode ou MindMapNode)
            if isinstance(item, (StyledNode, MindMapNode)):
                rect = item.sceneBoundingRect().adjusted(-10, -10, 10, 10)
                # Verificar se o retângulo intercepta a linha direta
                if self._line_intersects_rect_fast(start, end, rect):
                    obstacles.append(rect)
        
        return obstacles

    def _line_intersects_rect_fast(self, start, end, rect):
        """Verificação rápida de interseção linha-retângulo"""
        # Se um dos pontos está dentro do retângulo, não considerar interseção
        if rect.contains(start) or rect.contains(end):
            return False
        
        # Verificar interseção com as 4 bordas do retângulo
        lines = [
            (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
            (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
            (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
            (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top()))
        ]
        
        for p1, p2 in lines:
            if self._segments_intersect(start, end, p1, p2):
                return True
        
        return False

    def _segments_intersect(self, a1, a2, b1, b2):
        """Verifica se dois segmentos de linha se intersectam"""
        def ccw(A, B, C):
            return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())
        
        return ccw(a1, b1, b2) != ccw(a2, b1, b2) and ccw(a1, a2, b1) != ccw(a1, a2, b2)

    def _create_smooth_connection(self, start, end):
        """Cria uma conexão suave direta entre dois pontos"""
        path = QPainterPath()
        path.moveTo(start)
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 30:
            path.lineTo(end)
        else:
            # Curva suave com ponto de controle
            curvature = min(distance * 0.2, 40)
            perp_x = -dy / distance if distance > 0 else 0
            perp_y = dx / distance if distance > 0 else 0
            
            mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
            control = QPointF(
                mid.x() + perp_x * curvature,
                mid.y() + perp_y * curvature
            )
            path.quadTo(control, end)
        
        self.setPath(path)

    def _create_orthogonal_route(self, start, end, obstacles):
        """Cria rota ortogonal que desvia dos obstáculos"""
        if not obstacles:
            self._create_smooth_connection(start, end)
            return
        
        # Verificar se há obstáculos na linha direta
        has_obstacle_on_direct = False
        for rect in obstacles:
            if self._line_intersects_rect_fast(start, end, rect):
                has_obstacle_on_direct = True
                break
        
        if not has_obstacle_on_direct:
            self._create_smooth_connection(start, end)
            return
        
        # Calcular rota ortogonal com desvio
        dx = abs(end.x() - start.x())
        dy = abs(end.y() - start.y())
        
        points = [start]
        
        # Encontrar o melhor lado para desviar (acima ou abaixo dos obstáculos)
        detour_y = self._find_best_detour_y(start, end, obstacles)
        
        if dx > dy or dy == 0:
            # Movimento predominante horizontal ou horizontal puro
            # Rota: start -> (x intermediário, y original) -> (x intermediário, y desvio) -> (x intermediário, y final) -> end
            mid_x = (start.x() + end.x()) / 2
            
            # Ponto 1: Saída horizontal do start
            exit_x = start.x() + min(dx * 0.3, 100)
            p1 = QPointF(exit_x, start.y())
            points.append(p1)
            
            # Ponto 2: Subir/descer para o desvio
            p2 = QPointF(exit_x, detour_y)
            points.append(p2)
            
            # Ponto 3: Travessia horizontal no nível do desvio
            entry_x = end.x() - min(dx * 0.3, 100)
            p3 = QPointF(entry_x, detour_y)
            points.append(p3)
            
            # Ponto 4: Descer/subir para o nível final
            p4 = QPointF(entry_x, end.y())
            points.append(p4)
        else:
            # Movimento predominante vertical
            # Rota similar mas invertida
            mid_y = (start.y() + end.y()) / 2
            
            exit_y = start.y() + min(dy * 0.3, 100)
            p1 = QPointF(start.x(), exit_y)
            points.append(p1)
            
            detour_x = self._find_best_detour_x(start, end, obstacles)
            p2 = QPointF(detour_x, exit_y)
            points.append(p2)
            
            entry_y = end.y() - min(dy * 0.3, 100)
            p3 = QPointF(detour_x, entry_y)
            points.append(p3)
            
            p4 = QPointF(end.x(), entry_y)
            points.append(p4)
        
        points.append(end)
        
        # Criar caminho suave pelos pontos
        self._create_smooth_path_through_points(points)

    def _find_best_detour_y(self, start, end, obstacles):
        """Encontra o melhor Y para desviar dos obstáculos (acima ou abaixo)"""
        # Calcular limites dos obstáculos
        min_y = float('inf')
        max_y = float('-inf')
        
        for rect in obstacles:
            min_y = min(min_y, rect.top())
            max_y = max(max_y, rect.bottom())
        
        # Distâncias para desviar por cima ou por baixo
        margin = 30
        detour_above = min_y - margin
        detour_below = max_y + margin
        
        # Escolher o lado que está mais longe da linha atual
        current_y = (start.y() + end.y()) / 2
        dist_above = abs(detour_above - current_y)
        dist_below = abs(detour_below - current_y)
        
        if dist_above > dist_below:
            return detour_above
        else:
            return detour_below

    def _find_best_detour_x(self, start, end, obstacles):
        """Encontra o melhor X para desviar dos obstáculos (esquerda ou direita)"""
        min_x = float('inf')
        max_x = float('-inf')
        
        for rect in obstacles:
            min_x = min(min_x, rect.left())
            max_x = max(max_x, rect.right())
        
        margin = 30
        detour_left = min_x - margin
        detour_right = max_x + margin
        
        current_x = (start.x() + end.x()) / 2
        dist_left = abs(detour_left - current_x)
        dist_right = abs(detour_right - current_x)
        
        if dist_left > dist_right:
            return detour_left
        else:
            return detour_right

    def _point_in_obstacles(self, point, obstacles):
        """Verifica se um ponto está dentro de algum obstáculo"""
        for rect in obstacles:
            if rect.contains(point):
                return True
        return False

    def _create_smooth_path_through_points(self, points):
        """Cria caminho suave através de múltiplos pontos"""
        if len(points) < 2:
            return
        
        if len(points) == 2:
            self._create_smooth_connection(points[0], points[1])
            return
        
        path = QPainterPath()
        path.moveTo(points[0])
        
        # Criar curvas suaves entre segmentos
        for i in range(len(points) - 1):
            curr = points[i]
            next_p = points[i + 1]
            
            if i == 0:
                # Primeiro segmento
                self._add_smooth_segment(path, curr, next_p, True, False)
            elif i == len(points) - 2:
                # Último segmento
                self._add_smooth_segment(path, curr, next_p, False, True)
            else:
                # Segmentos do meio
                self._add_smooth_segment(path, curr, next_p, False, False)
        
        self.setPath(path)

    def _add_smooth_segment(self, path, start, end, is_first, is_last):
        """Adiciona segmento suave ao caminho"""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 20:
            path.lineTo(end)
            return
        
        # Suavizar as curvas nas conexões
        if is_first or is_last:
            # Curvas mais suaves nas extremidades
            curvature = min(distance * 0.3, 30)
        else:
            curvature = min(distance * 0.2, 20)
        
        # Vetor perpendicular
        perp_x = -dy / distance if distance > 0 else 0
        perp_y = dx / distance if distance > 0 else 0
        
        # Ponto de controle
        mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        control = QPointF(
            mid.x() + perp_x * curvature,
            mid.y() + perp_y * curvature
        )
        
        path.quadTo(control, end)

    def _update_path_advanced(self, start, end):
        """Sistema avançado com Shapely para detecção e scipy para curvas"""
        # Criar área proibida (união de todos os obstáculos)
        forbidden_areas = self._create_forbidden_areas(start, end)
        
        if not forbidden_areas:
            # Caminho direto - criar spline suave
            self._create_smooth_spline_path([start, end])
        else:
            # Caminho com obstáculos - usar A* avançado + spline
            path_points = self._find_path_shapely_astar(start, end, forbidden_areas)
            if path_points and len(path_points) > 2:
                self._create_smooth_spline_path(path_points)
            else:
                # Fallback para curva simples se A* falhar
                self._create_elegant_bezier_fallback(start, end)

    def _create_forbidden_areas(self, start, end):
        """Cria áreas proibidas usando Shapely"""
        if not self.source.scene() or not SHAPELY_AVAILABLE:
            return None
        
        # Expansão da área de busca
        margin = 50
        search_bounds = box(
            min(start.x(), end.x()) - margin,
            min(start.y(), end.y()) - margin,
            max(start.x(), end.x()) + margin,
            max(start.y(), end.y()) + margin
        )
        
        obstacles = []
        for item in self.source.scene().items():
            if item in (self, self.source, self.target):
                continue
                
            if hasattr(item, 'sceneBoundingRect'):
                rect = item.sceneBoundingRect()
                # Criar polígono Shapely para o obstáculo
                if 'Polygon' in globals():
                    poly = Polygon([
                        (rect.left(), rect.top()),
                        (rect.right(), rect.top()),
                        (rect.right(), rect.bottom()),
                        (rect.left(), rect.bottom())
                    ])
                else:
                    continue
                
                # Expandir ligeiramente o obstáculo (buffer)
                if hasattr(poly, 'buffer'):
                    expanded_poly = poly.buffer(5)  # 5 pixels de buffer
                    obstacles.append(expanded_poly)
                else:
                    obstacles.append(poly)
        
        if not obstacles:
            return None
        
        # Unir todos os obstáculos em uma área proibida
        if 'unary_union' in globals():
            forbidden_area = unary_union(obstacles)
        else:
            # Fallback simples: juntar geometrias manualmente
            forbidden_area = obstacles[0] if obstacles else None
        
        # Verificar se a área de busca intersecta os obstáculos
        if search_bounds.intersects(forbidden_area):
            return forbidden_area
        
        return None

    def _find_path_shapely_astar(self, start, end, forbidden_area):
        """Algoritmo A* usando geometria Shapely precisa"""
        # Criar grid de busca contornado aos obstáculos
        grid_resolution = 15  # pixels por célula
        
        # Limites da busca
        min_x = min(start.x(), end.x()) - 100
        max_x = max(start.x(), end.x()) + 100
        min_y = min(start.y(), end.y()) - 100
        max_y = max(start.y(), end.y()) + 100
        
        # Converter coordenadas para grid
        start_grid = (
            int((start.x() - min_x) / grid_resolution),
            int((start.y() - min_y) / grid_resolution)
        )
        end_grid = (
            int((end.x() - min_x) / grid_resolution),
            int((end.y() - min_y) / grid_resolution)
        )
        
        grid_width = int((max_x - min_x) / grid_resolution) + 1
        grid_height = int((max_y - min_y) / grid_resolution) + 1
        
        # Criar mapa de colisão usando Shapely
        collision_map = self._create_shapely_collision_map(
            min_x, min_y, grid_width, grid_height, 
            grid_resolution, forbidden_area
        )
        
        # Executar A* no grid
        path_grid = self._astar_shapely(
            start_grid, end_grid, collision_map, 
            grid_width, grid_height
        )
        
        if not path_grid:
            return [start, end]  # Fallback
        
        # Converter caminho do grid para coordenadas da cena
        path_scene = []
        for gx, gy in path_grid:
            scene_x = min_x + gx * grid_resolution + grid_resolution / 2
            scene_y = min_y + gy * grid_resolution + grid_resolution / 2
            path_scene.append(QPointF(scene_x, scene_y))
        
        return path_scene

    def _create_shapely_collision_map(self, min_x, min_y, width, height, 
                                    resolution, forbidden_area):
        """Cria mapa de colisão usando geometria precisa Shapely"""
        collision_map = [[False for _ in range(width)] for _ in range(height)]
        
        for gy in range(height):
            for gx in range(width):
                # Centro da célula em coordenadas da cena
                cell_center_x = min_x + gx * resolution + resolution / 2
                cell_center_y = min_y + gy * resolution + resolution / 2
                
                if 'Point' in globals():
                    cell_center = Point(cell_center_x, cell_center_y)
                
                # Verificar se célula intersecta área proibida
                if forbidden_area and hasattr(forbidden_area, 'intersects'):
                    if forbidden_area.intersects(cell_center):
                        collision_map[int(gy)][int(gx)] = True
                elif forbidden_area:
                    # Fallback simples
                    collision_map[int(gy)][int(gx)] = True
        
        return collision_map

    def _astar_shapely(self, start, end, collision_map, width, height):
        """A* otimizado para geometria Shapely"""
        def heuristic(a, b):
            return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        
        def get_neighbors(pos):
            x, y = pos
            neighbors = []
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,1), (1,-1), (-1,-1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and 
                    not collision_map[ny][nx]):
                    neighbors.append((nx, ny))
            return neighbors
        
        # A* implementation
        open_set = [(0, start)]
        came_from = {start: None}
        g_score = {start: 0}
        f_score = {start: heuristic(start, end)}
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current == end:
                # Reconstruir caminho
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                return list(reversed(path))
            
            for neighbor in get_neighbors(current):
                tentative_g = g_score[current] + heuristic(current, neighbor)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_set, (float(f_score[neighbor]), neighbor))
        
        return None

    def _create_smooth_spline_path(self, points):
        """Cria curvas suaves usando scipy.interpolate"""
        if len(points) < 2:
            return
        
        if len(points) == 2:
            # Para 2 pontos, criar curva Bezier simples
            self._create_elegant_bezier_fallback(points[0], points[1])
            return
        
        try:
            # Preparar pontos para spline
            points_array = np.array([(p.x(), p.y()) for p in points])
            
            # Verificar se pontos são colineares
            if len(points) == 3:
                # Testar colinearidade
                area = 0.5 * abs(
                    points_array[1, 0] * (points_array[2, 1] - points_array[0, 1]) +
                    points_array[2, 0] * (points_array[0, 1] - points_array[1, 1]) +
                    points_array[0, 0] * (points_array[1, 1] - points_array[2, 1])
                )
                if area < 100:  # Pontos quase colineares
                    self._create_elegant_bezier_fallback(points[0], points[-1])
                    return
            
            # Criar spline paramétrico
            if 'splprep' in globals() and 'splev' in globals():
                tck, u = splprep(points_array, s=0, k=min(3, len(points)-1))
                
                # Avaliar spline em mais pontos para curva suave
                u_new = np.linspace(0, 1, max(20, len(points) * 5))
                smooth_points = splev(u_new, tck)
            else:
                # Fallback sem scipy
                smooth_points = points_array
            
            # Criar QPainterPath a partir dos pontos suavizados
            path = QPainterPath()
            path.moveTo(QPointF(smooth_points[0][0], smooth_points[0][1]))
            
            for i in range(1, len(smooth_points)):
                path.lineTo(QPointF(smooth_points[i][0], smooth_points[i][1]))
            
            self.setPath(path)
            
        except Exception:
            # Fallback para Bezier se spline falhar
            self._create_elegant_bezier_fallback(points[0], points[-1])

    def _create_elegant_bezier_fallback(self, start, end):
        """Fallback elegante com curvas Bezier"""
        path = QPainterPath()
        path.moveTo(start)
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 30:
            path.lineTo(end)
        else:
            # Curvatura adaptativa
            curvature = min(distance * 0.25, 30)
            perp_x = -dy / distance if distance > 0 else 0
            perp_y = dx / distance if distance > 0 else 0
            
            mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
            control = QPointF(
                mid.x() + perp_x * curvature,
                mid.y() + perp_y * curvature
            )
            
            path.quadTo(control, end)
        
        self.setPath(path)

    def _update_path_fallback(self, start, end):
        """Fallback sem bibliotecas avançadas"""
        # Verificação simples de obstáculos
        obstacles = self._get_path_obstacles_simple(start, end)
        
        if not obstacles:
            self._create_elegant_bezier_fallback(start, end)
        else:
            # Roteamento simples sem Shapely
            waypoints = self._calculate_waypoints_fallback(start, end, obstacles)
            if waypoints:
                all_points = [start] + waypoints + [end]
                self._create_smooth_path_fallback(all_points)
            else:
                self._create_elegant_bezier_fallback(start, end)

    def _get_path_obstacles_simple(self, start, end):
        """Detecção simples de obstáculos sem Shapely"""
        if not self.source.scene():
            return []
        
        obstacles = []
        path_rect = QRectF(
            min(start.x(), end.x()) - 30,
            min(start.y(), end.y()) - 30,
            abs(end.x() - start.x()) + 60,
            abs(end.y() - start.y()) + 60
        )
        
        for item in self.source.scene().items(path_rect):
            if item in (self, self.source, self.target):
                continue
                
            if hasattr(item, 'sceneBoundingRect'):
                rect = item.sceneBoundingRect()
                if self._line_intersects_rect(start, end, rect):
                    obstacles.append(item)
        
        return obstacles

    def _calculate_waypoints_fallback(self, start, end, obstacles):
        """Cálculo simples de waypoints sem Shapely"""
        waypoints = []
        
        for obstacle in obstacles:
            rect = obstacle.sceneBoundingRect()
            center = rect.center()
            
            # Escolher lado para contornar (simplificado)
            if center.x() < (start.x() + end.x()) / 2:
                wp = QPointF(rect.left() - 30, center.y())
            else:
                wp = QPointF(rect.right() + 30, center.y())
            
            waypoints.append(wp)
        
        return waypoints

    def _create_smooth_path_fallback(self, points):
        """Cria caminho suave sem scipy"""
        if len(points) < 2:
            return
        
        path = QPainterPath()
        path.moveTo(points[0])
        
        for i in range(1, len(points)):
            curr = points[i-1]
            next_p = points[i]
            
            # Criar curva suave entre pontos
            dx = next_p.x() - curr.x()
            dy = next_p.y() - curr.y()
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 20:
                mid = QPointF(
                    (curr.x() + next_p.x()) / 2,
                    (curr.y() + next_p.y()) / 2
                )
                path.quadTo(mid, next_p)
            else:
                path.lineTo(next_p)
        
        self.setPath(path)

    def _get_path_obstacles(self, start, end):
        """Obtém lista de obstáculos no caminho entre start e end"""
        if not self.source.scene():
            return []
        
        obstacles = []
        # Margem maior para melhor detecção
        path_rect = self._get_path_bounds(start, end, margin=40)
        
        for item in self.source.scene().items(path_rect):
            if item in (self, self.source, self.target):
                continue
                
            if hasattr(item, 'sceneBoundingRect'):
                rect = item.sceneBoundingRect().adjusted(-5, -5, 5, 5)  # Pequena expansão
                if self._line_intersects_rect(start, end, rect):
                    obstacles.append(item)
        
        return obstacles

    def _get_path_bounds(self, start, end, margin=20):
        """Calcula retângulo que cobre o caminho com margem"""
        return QRectF(
            min(start.x(), end.x()) - margin,
            min(start.y(), end.y()) - margin,
            abs(end.x() - start.x()) + margin * 2,
            abs(end.y() - start.y()) + margin * 2
        )

    def _create_elegant_bezier_path(self, start, end):
        """Cria curva Bezier elegante para conexão direta"""
        path = QPainterPath()
        path.moveTo(start)
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 50:
            # Para conexões muito curtas, usar curva suave simples
            mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
            
            # Ponto de controle perpendicular para curvatura natural
            perp_x = -dy / distance if distance > 0 else 0
            perp_y = dx / distance if distance > 0 else 0
            
            curvature = min(distance * 0.15, 20)  # Curvatura proporcional à distância
            control = QPointF(
                mid.x() + perp_x * curvature,
                mid.y() + perp_y * curvature
            )
            
            path.quadTo(control, end)
        else:
            # Para conexões mais longas, usar curva cúbica mais elegante
            t = 0.5
            
            # Ponto médio
            mid = QPointF(start.x() + dx * t, start.y() + dy * t)
            
            # Vetor perpendicular para curvatura
            perp_x = -dy / distance if distance > 0 else 0
            perp_y = dx / distance if distance > 0 else 0
            
            # Curvatura adaptativa baseada na distância
            curvature = min(distance * 0.2, 40)
            
            # Dois pontos de controle para curva orgânica
            control1 = QPointF(
                start.x() + dx * 0.25 + perp_x * curvature * 0.5,
                start.y() + dy * 0.25 + perp_y * curvature * 0.5
            )
            control2 = QPointF(
                start.x() + dx * 0.75 + perp_x * curvature * 0.5,
                start.y() + dy * 0.75 + perp_y * curvature * 0.5
            )
            
            path.cubicTo(control1, control2, end)
        
        self.setPath(path)

    def _create_routed_bezier_path(self, start, end, obstacles):
        """Cria caminho com múltiplas curvas Bezier para contornar obstáculos"""
        # Encontrar waypoints para contornar obstáculos
        waypoints = self._calculate_bezier_waypoints(start, end, obstacles)
        
        if not waypoints:
            # Fallback para caminho direto
            self._create_elegant_bezier_path(start, end)
            return
        
        path = QPainterPath()
        path.moveTo(start)
        
        # Criar curvas suaves através dos waypoints
        all_points = [start] + waypoints + [end]
        
        for i in range(len(all_points) - 1):
            curr_point = all_points[i]
            next_point = all_points[i + 1]
            
            # Criar curva Bezier entre pontos consecutivos
            self._add_bezier_segment(path, curr_point, next_point, i == 0, i == len(all_points) - 2)
        
        self.setPath(path)

    def _calculate_bezier_waypoints(self, start, end, obstacles):
        """Calcula pontos de waypoin para roteamento com curvas"""
        if not obstacles:
            return []
        
        waypoints = []
        
        # Para cada obstáculo, calcular melhor rota de contorno
        for obstacle in obstacles:
            rect = obstacle.sceneBoundingRect()
            corners = self._get_rect_corners(rect)
            
            # Encontrar melhor ponto de passagem ao redor do obstáculo
            best_corner = None
            min_total_distance = float('inf')
            
            for corner in corners:
                # Distância total passando por este corner
                dist_start_corner = math.sqrt((corner.x() - start.x())**2 + (corner.y() - start.y())**2)
                dist_corner_end = math.sqrt((end.x() - corner.x())**2 + (end.y() - corner.y())**2)
                total_distance = dist_start_corner + dist_corner_end
                
                if total_distance < min_total_distance:
                    min_total_distance = total_distance
                    best_corner = corner
            
            if best_corner:
                # Adicionar waypoint com offset suave
                offset = 25  # Distância suave do obstáculo
                if best_corner.x() < rect.center().x():
                    best_corner = QPointF(best_corner.x() - offset, best_corner.y())
                elif best_corner.x() > rect.center().x():
                    best_corner = QPointF(best_corner.x() + offset, best_corner.y())
                
                if best_corner.y() < rect.center().y():
                    best_corner = QPointF(best_corner.x(), best_corner.y() - offset)
                elif best_corner.y() > rect.center().y():
                    best_corner = QPointF(best_corner.x(), best_corner.y() + offset)
                
                waypoints.append(best_corner)
        
        return waypoints

    def _get_rect_corners(self, rect):
        """Obtém os 4 cantos de um retângulo"""
        return [
            QPointF(rect.left(), rect.top()),      # Topo esquerdo
            QPointF(rect.right(), rect.top()),     # Topo direito
            QPointF(rect.right(), rect.bottom()),  # Base direita
            QPointF(rect.left(), rect.bottom())    # Base esquerda
        ]

    def _add_bezier_segment(self, path, start, end, is_first, is_last):
        """Adiciona segmento de curva Bezier suave entre dois pontos"""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 30:
            # Segmentos muito curtos: linha reta
            path.lineTo(end)
            return
        
        # Calcular curvatura baseada na posição (mais suave no meio)
        if is_first or is_last:
            curvature = distance * 0.3
        else:
            curvature = distance * 0.2
        
        # Vetor perpendicular
        perp_x = -dy / distance if distance > 0 else 0
        perp_y = dx / distance if distance > 0 else 0
        
        # Ponto de controle para curva suave
        mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        control = QPointF(
            mid.x() + perp_x * curvature,
            mid.y() + perp_y * curvature
        )
        
        path.quadTo(control, end)

    def _has_clear_path(self, start, end):
        """Verificação simplificada e precisa de caminho livre"""
        if not self.source.scene():
            return True
        
        # Criar linha entre start e end
        line_vector = QPointF(end.x() - start.x(), end.y() - start.y())
        line_length = math.sqrt(line_vector.x()**2 + line_vector.y()**2)
        
        if line_length == 0:
            return True
        
        # Normalizar vetor
        line_vector = QPointF(line_vector.x() / line_length, line_vector.y() / line_length)
        
        # Margem de verificação (afastar um pouco da linha)
        margin = 15
        
        for item in self.source.scene().items():
            if item in (self, self.source, self.target):
                continue
                
            if hasattr(item, 'sceneBoundingRect'):
                rect = item.sceneBoundingRect()
                
                # Verificar se o retângulo intersecta a linha
                if self._rect_line_intersection(rect, start, end, margin):
                    return False
        
        return True

    def _rect_line_intersection(self, rect, line_start, line_end, margin):
        """Verificação eficiente de interseção retângulo-linha"""
        # Expansão do retângulo com margem
        expanded_rect = rect.adjusted(-margin, -margin, margin, margin)
        
        # Se está muito distante, não intersecta
        rect_center = expanded_rect.center()
        line_center = QPointF((line_start.x() + line_end.x()) / 2, (line_start.y() + line_end.y()) / 2)
        
        dist_to_rect = math.sqrt(
            (rect_center.x() - line_center.x())**2 + 
            (rect_center.y() - line_center.y())**2
        )
        
        # Se centro do retângulo está longe da linha, não há interseção
        if dist_to_rect > max(expanded_rect.width(), expanded_rect.height()):
            return False
        
        # Verificação final de interseção borda a borda
        return self._line_intersects_rect(line_start, line_end, expanded_rect)

    def _find_path_astar(self, start, end):
        """Implementação do algoritmo A* para encontrar caminho ótimo"""
        if not self.source.scene():
            return [start, end]
        
        # Definir grid de busca (resolução de 20 pixels para performance)
        grid_size = 20
        bounds = self._get_search_bounds(start, end)
        
        # Converter para coordenadas de grid
        start_grid = (int(start.x() / grid_size), int(start.y() / grid_size))
        end_grid = (int(end.x() / grid_size), int(end.y() / grid_size))
        
        # Criar mapa de obstáculos
        obstacle_map = self._create_obstacle_map(bounds, grid_size)
        
        # A* search
        path = self._astar_search(start_grid, end_grid, obstacle_map, bounds, grid_size)
        
        if path:
            # Converter coordenadas de grid de volta para coordenadas de cena
            scene_points = [QPointF(x * grid_size + grid_size/2, y * grid_size + grid_size/2) 
                          for x, y in path]
            return scene_points
        
        return [start, end]

    def _get_search_bounds(self, start, end):
        """Define os limites da área de busca"""
        margin = 100
        min_x = min(start.x(), end.x()) - margin
        max_x = max(start.x(), end.x()) + margin
        min_y = min(start.y(), end.y()) - margin
        max_y = max(start.y(), end.y()) + margin
        
        return (min_x, min_y, max_x, max_y)

    def _create_obstacle_map(self, bounds, grid_size):
        """Cria um mapa de obstáculos para o A*"""
        min_x, min_y, max_x, max_y = bounds
        grid_width = int((max_x - min_x) / grid_size) + 1
        grid_height = int((max_y - min_y) / grid_size) + 1
        
        obstacle_map = [[False for _ in range(grid_width)] for _ in range(grid_height)]
        
        if not self.source.scene():
            return obstacle_map
        
        # Marcar células que contêm obstáculos
        for item in self.source.scene().items():
            if item in (self, self.source, self.target):
                continue
                
            if hasattr(item, 'sceneBoundingRect'):
                rect = item.sceneBoundingRect().adjusted(-10, -10, 10, 10)
                
                # Marcar células que intersectam o retângulo do obstáculo
                start_x = max(0, int((rect.left() - min_x) / grid_size))
                end_x = min(grid_width - 1, int((rect.right() - min_x) / grid_size))
                start_y = max(0, int((rect.top() - min_y) / grid_size))
                end_y = min(grid_height - 1, int((rect.bottom() - min_y) / grid_size))
                
                for y in range(start_y, end_y + 1):
                    for x in range(start_x, end_x + 1):
                        obstacle_map[int(y)][int(x)] = True
        
        return obstacle_map

    def _astar_search(self, start, end, obstacle_map, bounds, grid_size):
        """Executa a busca A* no grid"""
        min_x, min_y, max_x, max_y = bounds
        grid_width = int((max_x - min_x) / grid_size) + 1
        grid_height = int((max_y - min_y) / grid_size) + 1
        
        # Fila de prioridade (f_score, counter, node)
        counter = 0
        open_set = [(0.0, counter, start)]
        came_from = {}
        g_score = {start: 0.0}
        f_score = {start: self._heuristic(start, end)}
        
        while open_set:
            current_f, _, current = heapq.heappop(open_set)
            
            if current == end:
                # Reconstruir caminho
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return list(reversed(path))
            
            # Verificar vizinhos
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Verificar limites
                if (neighbor[0] < 0 or neighbor[0] >= grid_width or 
                    neighbor[1] < 0 or neighbor[1] >= grid_height):
                    continue
                
                # Verificar obstáculo
                if obstacle_map[neighbor[1]][neighbor[0]]:
                    continue
                
                # Calcular custos
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0  # Diagonal custa mais
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, end)
                    counter += 1
                    heapq.heappush(open_set, (float(f_score[neighbor]), counter, neighbor))
        
        return None  # Não encontrou caminho

    def _heuristic(self, a, b):
        """Heurística Euclidiana para A*"""
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.sqrt(dx*dx + dy*dy)

    def _create_smooth_path_from_points(self, points):
        """Cria um caminho suave a partir de uma lista de pontos"""
        if len(points) < 2:
            return
        
        path = QPainterPath()
        path.moveTo(points[0])
        
        if len(points) == 2:
            # Caminho direto com curva suave
            self._add_smooth_curve(path, points[0], points[1])
        else:
            # Múltiplos pontos - criar curvas suaves entre segmentos
            for i in range(len(points) - 1):
                if i == 0:
                    # Primeiro segmento: do início ao segundo ponto
                    self._add_smooth_curve(path, points[i], points[i + 1])
                elif i < len(points) - 2:
                    # Segmentos do meio: usar ponto de controle suave
                    curr = points[i]
                    next_p = points[i + 1]
                    
                    # Ponto de controle para curva suave
                    control = QPointF(
                        (curr.x() + next_p.x()) / 2,
                        (curr.y() + next_p.y()) / 2
                    )
                    path.quadTo(control, next_p)
                else:
                    # Último segmento
                    self._add_smooth_curve(path, points[i], points[i + 1])
        
        self.setPath(path)

    def _create_smooth_curved_path(self, start, end):
        """Cria um caminho com curvas suaves entre dois pontos"""
        path = QPainterPath()
        path.moveTo(start)
        self._add_smooth_curve(path, start, end)
        self.setPath(path)

    def _add_smooth_curve(self, path, start, end):
        """Adiciona uma curva Bezier suave ao caminho"""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 30:
            # Para distâncias muito curtas, usar linha reta
            path.lineTo(end)
            return
        
        # Calcular pontos de controle para curva suave
        curvature = min(0.3, 50.0 / distance)
        
        # Vetor perpendicular para criar curva
        perp_x = -dy / distance
        perp_y = dx / distance
        
        # Curvatura baseada na distância
        curve_amount = distance * curvature
        
        # Dois pontos de controle para curva mais suave
        control1 = QPointF(
            start.x() + dx * 0.25 + perp_x * curve_amount * 0.5,
            start.y() + dy * 0.25 + perp_y * curve_amount * 0.5
        )
        control2 = QPointF(
            start.x() + dx * 0.75 - perp_x * curve_amount * 0.5,
            start.y() + dy * 0.75 - perp_y * curve_amount * 0.5
        )
        
        path.cubicTo(control1, control2, end)

    def _line_intersects_rect(self, start, end, rect):
        """Verifica se uma linha intercepta um retângulo"""
        if rect.contains(start) or rect.contains(end):
            return False
        
        # Pontos das bordas do retângulo
        corners = [
            QPointF(rect.left(), rect.top()),
            QPointF(rect.right(), rect.top()),
            QPointF(rect.right(), rect.bottom()),
            QPointF(rect.left(), rect.bottom())
        ]
        
        # Verificar interseção com cada borda
        for i in range(4):
            p1 = corners[i]
            p2 = corners[(i + 1) % 4]
            
            if self._lines_intersect(start, end, p1, p2):
                return True
        
        return False

    def _lines_intersect(self, p1, p2, p3, p4):
        """Verifica se duas linhas se intersectam"""
        def ccw(A, B, C):
            return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        # NÃO chamar update_path() aqui - causa loop infinito
        # A linha é atualizada apenas quando necessário (movimento de nós)
        
        # Destacar quando selecionado
        if option.state & QStyle.State_Selected:
            pen = self.pen()
            pen.setColor(QColor("#ff6b35"))  # Laranja para seleção
            pen.setWidth(5)
            self.setPen(pen)
        else:
            self.setPen(QPen(QColor("#0078d4"), 3, Qt.SolidLine, Qt.RoundCap))
        
        super().paint(painter, option, widget)