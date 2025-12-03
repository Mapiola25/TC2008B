from mesa.discrete_space import CellAgent, FixedAgent
import random
from collections import Counter
import heapq
from typing import List, Tuple, Optional

destinations = []

def heuristic(cell1, cell2):
    """
    Calcula la distancia de Manhattan entre dos celdas.

    Args:
        cell1: Celda de origen
        cell2: Celda de destino

    Returns:
        float: Distancia de Manhattan
    """
    x1, y1 = cell1.coordinate
    x2, y2 = cell2.coordinate
    return abs(x1 - x2) + abs(y1 - y2)

class Car(CellAgent):
    """
    Agent that moves randomly.
    """
    def __init__(self, model, cell):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)

        # VALIDAcion verificamos que haya destino antes de asignar ubno
        if not destinations:
            raise ValueError("No hay destinos disponibles. El modelo no se inicializó correctamente.")

        self.destination = random.choice(destinations)
        self.cell = cell
        self.path = None  # Ruta calculada por A*
        self.path_index = 0  # Índice actual en la ruta
        self.stuck_counter = 0  # Contador de pasos bloqueado

        print(f"[CAR {self.unique_id}] Creado en {self.cell.coordinate} -> Destino: {self.destination.coordinate}")

    def get_orthogonal_neighbors(self, cell):
        """
        Obtiene solo los vecinos ortogonales (arriba, abajo, izquierda, derecha).
        Filtra vecinos diagonales del neighborhood de Mesa.

        Args:
            cell: Celda de la cual obtener vecinos

        Returns:
            List[Cell]: Lista de celdas vecinas ortogonales (máximo 4)
        """
        orthogonal_neighbors = []
        current_x, current_y = cell.coordinate

        # Solo considerar las 4 direcciones IZQUIERDA DERECHA ARRIBA ABAJO
        potential_neighbors = [
            (current_x + 1, current_y),  # RIGHT
            (current_x - 1, current_y),  # LEFT
            (current_x, current_y + 1),  # UP
            (current_x, current_y - 1),  # DOWN
        ]

        for neighbor in cell.neighborhood:
            # Solo agregar si está en las posiciones ortogonales
            if neighbor.coordinate in potential_neighbors:
                orthogonal_neighbors.append(neighbor)

        return orthogonal_neighbors

    def reconstruct_path(self, parent_map, current_cell):
        """
        Reconstruye la ruta desde el inicio hasta el destino.

        Args:
            parent_map: Diccionario de padres
            current_cell: Celda final (destino)

        Returns:
            List[Cell]: Ruta completa desde inicio hasta destino
        """
        path = [current_cell] # La celula atual la pasamos
        current_coord = current_cell.coordinate # Extraemos coordenada de cell

        while current_coord in parent_map:
            current_cell = parent_map[current_coord]
            path.append(current_cell) # Iteramos mandando las diferentes celulas a la lista (nos la dará en orden inverso)
            current_coord = current_cell.coordinate # Cambiamos coordenada actual

        path.reverse()
        return path

    def aStar(self, avoid_cars=False):
        """
        Implementa el algoritmo A* para encontrar la ruta óptima al destino.

        Args:
            avoid_cars: Si es True, evita celdas con coches (útil para recalcular rutas)

        Returns:
            List[Cell]: Lista de celdas que forman la ruta óptima, o None si no hay ruta
        """
        start = self.cell
        goal = self.destination

        # Verificar si ya estamos en el destino (comparar por coordenadas)
        if start.coordinate == goal.coordinate:
            return [start]

        # Debug: información de inicio (solo para debugging)
        # start_road = None
        # for agent in start.agents:
        #     if isinstance(agent, Road):
        #         start_road = agent
        #         break
        # print(f"[A*] Inicio: {start.coordinate}, Road: {start_road.direction if start_road else 'None'}, Destino: {goal.coordinate}")

        # Inicializar estructuras de datos
        open_set = []
        closed_set = set()

        # Diccionarios para almacenar g, h, f y parents
        g_score = {start.coordinate: 0}
        f_score = {start.coordinate: heuristic(start, goal)}
        parent_map = {}

        # Agregar nodo inicial a open_set
        heapq.heappush(open_set, (f_score[start.coordinate], start.coordinate, start)) # Grafo

        explored_count = 0
        while open_set:
            # Obtener el nodo con menor f_score
            result = heapq.heappop(open_set)
            current_f = result[0]
            current_coord = result[1]
            current_cell = result[2]

            explored_count += 1

            # Si llegamos al destino, reconstruir ruta (comparar por coordenadas)
            if current_cell.coordinate == goal.coordinate:
                path = self.reconstruct_path(parent_map, current_cell)
                print(f"[A*] ✓ Ruta encontrada desde {start.coordinate} a {goal.coordinate}")
                print(f"[A*] Longitud de ruta: {len(path)} pasos")
                print(f"[A*] Primera celda: {path[0].coordinate}, Última celda: {path[-1].coordinate}")
                print(f"[A*] ¿Última celda es destino? {path[-1].coordinate == goal.coordinate}")
                return path

            # Marcar como explorado
            closed_set.add(current_coord)

            # Explorar vecinos ORTOGONALES únicamente (no diagonales)
            neighbors_checked = 0
            neighbors_valid = 0
            orthogonal_neighbors = self.get_orthogonal_neighbors(current_cell)

            for neighbor in orthogonal_neighbors:
                neighbor_coord = neighbor.coordinate
                neighbors_checked += 1

                # Saltar si ya fue explorado
                if neighbor_coord in closed_set:
                    continue

                # Calcular dirección del movimiento
                direction = self.get_direction(current_cell, neighbor)

                # Ponemos none porque direction no contempla movimientos diagonales
                if direction is None:
                    continue

                # Caso especial: Si estamos en la celda de inicio (spawn point),
                # permitir moverse en cualquier dirección para el primer paso (comparar por coordenadas)
                is_first_move = (current_cell.coordinate == start.coordinate)

                if is_first_move:
                    # Desde spawn point, solo verificar que la celda destino sea transitable
                    # sin restricción de dirección
                    if not self.is_walkable(neighbor, None, goal, allow_lane_change=True, check_cars=avoid_cars, from_cell=current_cell):
                        continue
                else:
                    # Después del primer movimiento, verificar dirección estrictamente
                    if not self.is_walkable(neighbor, direction, goal, allow_lane_change=True, check_cars=avoid_cars, from_cell=current_cell):
                        continue

                neighbors_valid += 1

                # Verificar si estamos en spawn point o destination para penalizaciones de costo (comparar por coordenadas)
                is_spawn_or_destination = current_cell.coordinate == start.coordinate or any(
                    isinstance(agent, Destination) for agent in current_cell.agents
                )

                # Calcular nuevo g_score con penalización por cambio de carril
                base_cost = 1

                # Penalizar cambios de carril para priorizar seguir adelante
                if not is_spawn_or_destination and self.is_lane_change(current_cell, neighbor):
                    # Agregar penalización alta para cambio de carril (hace que sea menos preferido)
                    base_cost += 15  # Penalización significativa

                tentative_g = g_score[current_coord] + base_cost

                # Si encontramos un mejor camino a este vecino
                if neighbor_coord not in g_score or tentative_g < g_score[neighbor_coord]:
                    # Actualizar valores
                    parent_map[neighbor_coord] = current_cell
                    g_score[neighbor_coord] = tentative_g
                    h = heuristic(neighbor, goal)
                    f_score[neighbor_coord] = tentative_g + h

                    # Agregar a open_set si no está
                    if neighbor_coord not in [item[1] for item in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor_coord], neighbor_coord, neighbor))

        # No se encontró ruta
        print(f"[A*] ERROR: No se encontró ruta desde {start.coordinate} hasta {goal.coordinate} (explorados: {explored_count} nodos)")
        return None

    def get_direction(self, from_cell, to_cell):
        """
        Calcula la dirección del movimiento entre dos celdas.
        Solo permite movimientos ortogonales (arriba, abajo, izquierda, derecha).
        Rechaza movimientos diagonales o no adyacentes.

        Args:
            from_cell: Celda de origen
            to_cell: Celda de destino

        Returns:
            str: Dirección ("Up", "Down", "Left", "Right") o None si es diagonal/inválido
        """
        dx = to_cell.coordinate[0] - from_cell.coordinate[0]
        dy = to_cell.coordinate[1] - from_cell.coordinate[1]

        # Verificar que sea un movimiento adyacente (distancia Manhattan = 1)
        manhattan_distance = abs(dx) + abs(dy)
        if manhattan_distance != 1:
            # Rechazar movimientos no adyacentes o diagonales
            return None

        # Solo permitir movimientos ortogonales (un solo eje cambia)
        if dx > 0 and dy == 0:
            return "Right"
        elif dx < 0 and dy == 0:
            return "Left"
        elif dy > 0 and dx == 0:
            return "Up"
        elif dy < 0 and dx == 0:
            return "Down"

        # Si llegamos aquí, es un movimiento diagonal o inválido
        return None

    def is_lane_change(self, from_cell, to_cell):
        """
        Detecta si un movimiento es un cambio de carril (lateral) o seguir adelante.

        Args:
            from_cell: Celda de origen
            to_cell: Celda de destino

        Returns:
            bool: True si es cambio de carril (movimiento lateral), False si es adelante
        """
        # Obtener la dirección del Road en la celda actual
        road_agent = None
        for agent in from_cell.agents:
            if isinstance(agent, Road):
                road_agent = agent
                break

        # Si no hay Road, no es cambio de carril
        if not road_agent:
            return False

        # Obtener dirección del movimiento
        movement_direction = self.get_direction(from_cell, to_cell)

        # SEGURIDAD: Si el movimiento es None (diagonal), no procesar
        if movement_direction is None:
            return False

        # Si el movimiento es Left o Right, es cambio de carril
        # (asumiendo que las calles van Up/Down principalmente)
        # Esto puede ajustarse según la configuración de tu mapa
        if movement_direction in ["Left", "Right"]:
            # Verificar si la dirección del road es Up o Down
            if road_agent.direction in ["Up", "Down"]:
                return True  # Es cambio de carril
        elif movement_direction in ["Up", "Down"]:
            # Verificar si la dirección del road es Left o Right
            if road_agent.direction in ["Left", "Right"]:
                return True  # Es cambio de carril

        return False  # Es movimiento adelante en el carril

    def is_walkable(self, cell, direction_from_parent=None, goal=None, allow_lane_change=True, check_cars=False, from_cell=None):
        """
        Verifica si un coche puede moverse a una celda específica.

        Args:
            cell: Celda a verificar
            direction_from_parent: Dirección desde la celda padre
            goal: Celda de destino (para permitir siempre llegar al destino)
            allow_lane_change: Si es True, permite movimientos laterales (cambio de carril)
            check_cars: Si es True, penaliza celdas con coches (para recalculación de rutas)
            from_cell: Celda de origen (para verificar cambios de carril válidos)

        Returns:
            bool: True si la celda es transitable
        """
        # PRIORIDAD MÁXIMA: Si esta celda es el destino final, SIEMPRE permitir el movimiento
        # Los coches deben poder llegar a su destino desde cualquier dirección (comparar por coordenadas)
        if goal and cell.coordinate == goal.coordinate:
            # Verificar que no haya obstáculo en el destino
            has_obstacle = any(isinstance(agent, Obstacle) for agent in cell.agents)
            if not has_obstacle:
                print(f"[WALKABLE] ✓ Destino {cell.coordinate} ES ALCANZABLE (sin obstáculos)")
                return True
            else:
                print(f"[WALKABLE] ✗ ERROR: Destino {cell.coordinate} tiene obstáculo!")
                return False

        # Buscar agentes en la celda
        road_agent = None
        traffic_light = None
        has_obstacle = False
        has_destination = False
        has_car = False

        for agent in cell.agents:
            if isinstance(agent, Road):
                road_agent = agent
            elif isinstance(agent, Traffic_Light):
                traffic_light = agent
            elif isinstance(agent, Obstacle):
                has_obstacle = True
            elif isinstance(agent, Destination):
                has_destination = True
            elif isinstance(agent, Car) and check_cars:
                has_car = True

        # No se puede pasar por obstáculos
        if has_obstacle:
            return False

        # Si hay un coche y estamos verificando coches, no es transitable
        # (esto ayuda a recalcular rutas evitando coches bloqueando)
        if has_car and check_cars:
            return False

        # Si hay un destino en esta celda, SIEMPRE es transitable
        # Los coches deben poder llegar a cualquier celda de destino
        if has_destination:
            # print(f"[WALKABLE] Celda con Destination {cell.coordinate} es transitable")
            return True

        # Debe haber una calle
        if not road_agent:
            return False

        # Verificar dirección si se especifica
        if direction_from_parent:
            # Caso especial: Si la celda origen no tiene Road (spawn point o destination)
            # permitir entrar a cualquier Road adyacente sin restricción de dirección
            if from_cell:
                from_has_road = any(isinstance(agent, Road) for agent in from_cell.agents)
                if not from_has_road:
                    # Estamos saliendo de un spawn point o destination
                    # Permitir entrar a cualquier Road adyacente
                    return True

            # REGLA PRINCIPAL: Verificar que NO estemos yendo en SENTIDO CONTRARIO
            # Se considera sentido contrario cuando:
            # - Movimiento es "Up" y Road es "Down" (o viceversa)
            # - Movimiento es "Left" y Road es "Right" (o viceversa)

            opposite_directions = {
                "Up": "Down",
                "Down": "Up",
                "Left": "Right",
                "Right": "Left"
            }

            # Si estamos intentando ir en sentido contrario al Road, RECHAZAR
            if opposite_directions.get(direction_from_parent) == road_agent.direction:
                return False

            # Si la dirección coincide exactamente, PERMITIR (movimiento adelante)
            if road_agent.direction == direction_from_parent:
                return True

            # Si llegamos aquí, es un movimiento perpendicular (giro)
            # Los giros están permitidos (por ejemplo, de calle "Right" a calle "Up")
            # Solo verificamos que no sea sentido contrario (ya verificado arriba)
            return True

        return True

    def move(self):
        """
        Mueve el coche siguiendo la ruta calculada por A*.
        Recalcula la ruta si está bloqueado por mucho tiempo para buscar cambios de carril.
        """
        # PRIMERO: Verificar si ya estamos en el destino (comparar por COORDENADAS)
        # Esto debe estar ANTES de cualquier otra lógica
        current_coord = self.cell.coordinate
        dest_coord = self.destination.coordinate

        # DEBUG: Logging detallado para algunos coches
        if self.unique_id in [626, 630, 632, 634, 638, 650, 655, 659]:
            
            # Verificar si estamos en ALGUNA celda de Destination
            has_any_dest = any(isinstance(agent, Destination) for agent in self.cell.agents)
            

        if current_coord == dest_coord:
            self.model.cars_arrived += 1

            # IMPORTANTE: Primero sacar el coche de la celda

            if self.cell is not None:
                self.cell.remove_agent(self)

            # Luego eliminar el coche del modelo
            self.model.agents.remove(self)
            return

        # Si no hay ruta calculada, calcularla
        if self.path is None:
            print(f"[CAR {self.unique_id}] Calculando ruta desde {current_coord} a {dest_coord}")
            self.path = self.aStar()
            if self.path is None:
                
                return
            self.path_index = 0
            

        # Si ya llegamos al final de la ruta
        if self.path_index >= len(self.path) - 1:
            # Verificar si la última celda es el destino (comparar por coordenadas)
            if self.path[-1].coordinate == self.destination.coordinate:
               
               
                # Continuar para moverse al destino si aún no estamos ahí
                if self.cell.coordinate == self.destination.coordinate:
                    return
            else:
               
                self.path = None
                return

        # Si estamos bloqueados por mucho tiempo, recalcular ruta para buscar alternativas
        if self.stuck_counter >= 3:
            print(f"[CAR {self.unique_id}] Bloqueado en {self.cell.coordinate}, recalculando ruta...")
            # Recalcular evitando coches para buscar cambios de carril
            self.path = self.aStar(avoid_cars=True)
            if self.path is None:
                # Si no encuentra ruta evitando coches, intentar sin evitarlos
                
                self.path = self.aStar(avoid_cars=False)
                if self.path is None:
                    
                    return
            self.path_index = 0
            self.stuck_counter = 0

        # Siguiente celda en la ruta
        next_cell = self.path[self.path_index + 1]

        # Verificar si la siguiente celda es el destino (comparar por coordenadas)
        is_next_destination = (next_cell.coordinate == self.destination.coordinate)
        if is_next_destination:
            print(f"[CAR {self.unique_id}] ⭐ Siguiente celda ES EL DESTINO {next_cell.coordinate}")

        # SEGURIDAD 1: Verificar que el movimiento sea ortogonal (no diagonal)
        current_x, current_y = self.cell.coordinate
        next_x, next_y = next_cell.coordinate
        dx = abs(next_x - current_x)
        dy = abs(next_y - current_y)

        # Un movimiento válido debe tener exactamente 1 paso en un solo eje
        if dx + dy != 1:
            
            # Recalcular ruta ya que algo salió mal
            self.path = None
            return

        # SEGURIDAD 2: Verificar dirección del movimiento
        movement_direction = self.get_direction(self.cell, next_cell)
        if movement_direction is None:
            print(f"[CAR {self.unique_id}] ERROR: Dirección de movimiento inválida desde {self.cell.coordinate} a {next_cell.coordinate}")
            # Recalcular ruta ya que algo salió mal
            self.path = None
            return

        # Verificar que el movimiento sigue siendo válido según las reglas de tráfico
        is_walkable = self.is_walkable(next_cell, movement_direction, self.destination, from_cell=self.cell)



        if not is_walkable:
            print(f"[CAR {self.unique_id}] ERROR: Movimiento inválido desde {self.cell.coordinate} a {next_cell.coordinate} (dir: {movement_direction})")
            if is_next_destination:
                print(f"[CAR {self.unique_id}] ⚠️ CRÍTICO: ¡El destino está marcado como NO WALKABLE!")
            # La ruta ya no es válida, recalcular
            self.path = None
            return

        # Verificar si hay semáforo en la siguiente celda
        traffic_light = None
        for agent in next_cell.agents:
            if isinstance(agent, Traffic_Light):
                traffic_light = agent
                break

        # Si hay semáforo y está en rojo, esperar
        if traffic_light and not traffic_light.state:
            if self.stuck_counter % 10 == 0:  # Log cada 10 pasos
                print(f"[CAR {self.unique_id}] Esperando semáforo en rojo en {next_cell.coordinate}")
            self.stuck_counter += 1
            return

        # Verificar si hay otro coche en la siguiente celda
        has_car = any(isinstance(agent, Car) for agent in next_cell.agents)
        if has_car:
            if is_next_destination:
                print(f"[CAR {self.unique_id}] ⚠️ HAY OTRO COCHE EN EL DESTINO {next_cell.coordinate}!")
                cars_in_dest = [agent for agent in next_cell.agents if isinstance(agent, Car)]
                for car in cars_in_dest:
                    print(f"  - Car {car.unique_id} en destino")
            if self.stuck_counter % 10 == 0:  # Log cada 10 pasos
                print(f"[CAR {self.unique_id}] Esperando a otro coche en {next_cell.coordinate} (bloqueado {self.stuck_counter+1} pasos)")
            self.stuck_counter += 1
            return

        # Moverse a la siguiente celda
        self.move_to(next_cell)
        
        self.path_index += 1
        self.stuck_counter = 0  # Resetear contador al moverse exitosamente

    def step(self):
        """ 
        Determines the new direction it will take, and then moves
        """
        self.move()
        

class Traffic_Light(FixedAgent):
    """
    Traffic light. Where the traffic lights are in the grid.
    """
    def __init__(self, model, cell, state = False, timeToChange = 10):
        """
        Creates a new Traffic light.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
            state: Whether the traffic light is green or red
            timeToChange: After how many step should the traffic light change color 
        """
        super().__init__(model)
        self.cell = cell
        self.state = state
        self.timeToChange = timeToChange

    def step(self):
        """
        To change the state (green or red) of the traffic light in case you consider the time to change of each traffic light.
        """
        if self.model.current_step % self.timeToChange == 0:
            self.state = not self.state

class Destination(FixedAgent):
    """
    Destination agent. Where each car should go.
    """
    def __init__(self, model, cell):
        """
        Creates a new destination agent
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)
        self.cell = cell
        destinations.append(self.cell)


class Obstacle(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        """
        Creates a new obstacle.
        
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)
        self.cell = cell

class Road(FixedAgent):
    """
    Road agent. Determines where the cars can move, and in which direction.
    """
    def __init__(self, model, cell, direction= "Left"):
        """
        Creates a new road.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model)
        self.cell = cell
        self.direction = direction
