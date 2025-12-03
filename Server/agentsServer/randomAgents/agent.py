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

        # Atributos para manejar crashes con Borrachito
        self.crashed = False
        self.crash_timer = 0
        self.original_position = cell

        print(f"[UNIT {self.unique_id}] Init at {self.cell.coordinate}")

    def get_orthogonal_neighbors(self, cell):
        """
        Obtiene vecinos ortogonales y diagonales para pathfinding.
        Los vecinos ortogonales permiten seguir adelante en el carril.
        Los vecinos diagonales permiten cambios de carril realistas.

        Args:
            cell: Celda de la cual obtener vecinos

        Returns:
            List[Cell]: Lista de celdas vecinas (ortogonales y diagonales, máximo 8)
        """
        valid_neighbors = []
        current_x, current_y = cell.coordinate

        # Vecinos ortogonales (4 direcciones) - para seguir adelante
        orthogonal_coords = [
            (current_x + 1, current_y),  # RIGHT
            (current_x - 1, current_y),  # LEFT
            (current_x, current_y + 1),  # UP
            (current_x, current_y - 1),  # DOWN
        ]

        # Vecinos diagonales (4 direcciones) - para cambios de carril
        diagonal_coords = [
            (current_x + 1, current_y + 1),  # UP-RIGHT
            (current_x - 1, current_y + 1),  # UP-LEFT
            (current_x + 1, current_y - 1),  # DOWN-RIGHT
            (current_x - 1, current_y - 1),  # DOWN-LEFT
        ]

        all_valid_coords = orthogonal_coords + diagonal_coords

        for neighbor in cell.neighborhood:
            if neighbor.coordinate in all_valid_coords:
                valid_neighbors.append(neighbor)

        return valid_neighbors

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

        # Debug: verificar spawn point (solo para debugging)
        # has_road_at_start = any(isinstance(agent, Road) for agent in start.agents)
        # print(f"[A*] Unit {self.unique_id} pathfinding:")
        # print(f"  From: {start.coordinate} (has Road: {has_road_at_start})")
        # print(f"  To: {goal.coordinate}")

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
                print(f"[PATH] Route found: {start.coordinate} to {goal.coordinate}")
                print(f"[PATH] Length: {len(path)} steps")
                return path

            # Marcar como explorado
            closed_set.add(current_coord)

            # Explorar vecinos (ortogonales y diagonales)
            neighbors_checked = 0
            neighbors_valid = 0
            all_neighbors = self.get_orthogonal_neighbors(current_cell)

            # Debug: log para spawn point (comentado para reducir ruido en logs)
            # is_start = (current_cell.coordinate == start.coordinate)
            # if is_start:
            #     print(f"  Exploring from spawn: {len(all_neighbors)} neighbors found")

            for neighbor in all_neighbors:
                neighbor_coord = neighbor.coordinate
                neighbors_checked += 1

                # Saltar si ya fue explorado
                if neighbor_coord in closed_set:
                    continue

                # Calcular dirección del movimiento
                direction = self.get_direction(current_cell, neighbor)

                # Si no es un movimiento válido, continuar
                if direction is None:
                    # if is_start:
                    #     print(f"    {neighbor_coord}: Invalid direction")
                    continue

                # Caso especial: Si estamos en la celda de inicio (spawn point),
                # permitir moverse en cualquier dirección para el primer paso (comparar por coordenadas)
                is_first_move = (current_cell.coordinate == start.coordinate)

                if is_first_move:
                    # Desde spawn point, solo verificar que la celda destino sea transitable
                    # sin restricción de dirección
                    walkable = self.is_walkable(neighbor, None, goal, allow_lane_change=True, check_cars=avoid_cars, from_cell=current_cell)
                    # if is_start:
                    #     has_road = any(isinstance(agent, Road) for agent in neighbor.agents)
                    #     print(f"    {neighbor_coord} dir={direction}: walkable={walkable}, has_road={has_road}")
                    if not walkable:
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
                    # Agregar penalización moderada para cambio de carril
                    # (prefiere seguir adelante, pero no bloquea cambios necesarios)
                    base_cost += 2  # Penalización moderada

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

            # Debug: log de vecinos válidos desde spawn (comentado)
            # if is_start:
            #     print(f"  Valid neighbors from spawn: {neighbors_valid}/{neighbors_checked}")

        # No path found
        print(f"[PATH] No route: {start.coordinate} to {goal.coordinate} ({explored_count} nodes)")
        return None

    def get_direction(self, from_cell, to_cell):
        """
        Calcula la dirección del movimiento entre dos celdas.
        Permite movimientos ortogonales (arriba, abajo, izquierda, derecha) y
        movimientos diagonales para cambios de carril realistas.

        Args:
            from_cell: Celda de origen
            to_cell: Celda de destino

        Returns:
            str: Dirección ("Up", "Down", "Left", "Right", "UpRight", "UpLeft",
                 "DownRight", "DownLeft") o None si es inválido
        """
        dx = to_cell.coordinate[0] - from_cell.coordinate[0]
        dy = to_cell.coordinate[1] - from_cell.coordinate[1]

        # Movimientos ortogonales (distancia Manhattan = 1)
        if abs(dx) + abs(dy) == 1:
            if dx > 0 and dy == 0:
                return "Right"
            elif dx < 0 and dy == 0:
                return "Left"
            elif dy > 0 and dx == 0:
                return "Up"
            elif dy < 0 and dx == 0:
                return "Down"

        # Movimientos diagonales (distancia Manhattan = 2, para cambios de carril)
        elif abs(dx) + abs(dy) == 2 and abs(dx) == 1 and abs(dy) == 1:
            if dx > 0 and dy > 0:
                return "UpRight"
            elif dx < 0 and dy > 0:
                return "UpLeft"
            elif dx > 0 and dy < 0:
                return "DownRight"
            elif dx < 0 and dy < 0:
                return "DownLeft"

        # Movimiento inválido (no adyacente o demasiado lejos)
        return None

    def is_lane_change(self, from_cell, to_cell):
        """
        Detecta si un movimiento es un cambio de carril o seguir adelante.
        Los movimientos diagonales son siempre cambios de carril.

        Args:
            from_cell: Celda de origen
            to_cell: Celda de destino

        Returns:
            bool: True si es cambio de carril, False si es adelante
        """
        # Obtener dirección del movimiento
        movement_direction = self.get_direction(from_cell, to_cell)

        # SEGURIDAD: Si el movimiento es None, no es válido
        if movement_direction is None:
            return False

        # Los movimientos diagonales SIEMPRE son cambios de carril
        if movement_direction in ["UpRight", "UpLeft", "DownRight", "DownLeft"]:
            return True

        # Para movimientos ortogonales, verificar si es perpendicular al Road
        road_agent = None
        for agent in from_cell.agents:
            if isinstance(agent, Road):
                road_agent = agent
                break

        # Si no hay Road, no es cambio de carril
        if not road_agent:
            return False

        # Si el movimiento es Left o Right, es cambio de carril
        # (asumiendo que las calles van Up/Down principalmente)
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
                print(f"[NAV] Target {cell.coordinate} accessible")
                return True
            else:
                print(f"[NAV] Target {cell.coordinate} blocked")
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
            # Caso especial: Si la celda origen es un spawn point o destination
            # permitir salir en cualquier dirección (incluso diagonal)
            if from_cell:
                # Verificar si es spawn point (no tiene Road) o destination
                from_has_road = any(isinstance(agent, Road) for agent in from_cell.agents)
                from_has_destination = any(isinstance(agent, Destination) for agent in from_cell.agents)

                # SPAWN POINTS: Las esquinas del mapa (0,0), (23,0), (0,24), (23,24)
                spawn_points = [(0, 0), (23, 0), (0, 24), (23, 24)]
                is_spawn_point = from_cell.coordinate in spawn_points

                # Si estamos saliendo de un spawn point o destination, permitir cualquier dirección
                if is_spawn_point or from_has_destination or not from_has_road:
                    # Estamos saliendo de un spawn point o destination
                    # Permitir entrar a cualquier Road adyacente
                    return True


            if direction_from_parent in ["UpRight", "UpLeft", "DownRight", "DownLeft"]:
                # Los movimientos diagonales deben avanzar en la dirección del Road
                # mientras se cambian de carril lateralmente

                # Extraer componentes del movimiento diagonal
                vertical_component = "Up" if "Up" in direction_from_parent else "Down"
                horizontal_component = "Right" if "Right" in direction_from_parent else "Left"

                # Diccionario de direcciones opuestas
                opposite_directions = {
                    "Up": "Down",
                    "Down": "Up",
                    "Left": "Right",
                    "Right": "Left"
                }

                # REGLA: El movimiento diagonal es válido si al menos UNA de sus componentes
                # coincide con la dirección del Road (y ninguna va en sentido contrario)

                # Verificar si alguna componente va en sentido contrario al Road
                vertical_opposite = opposite_directions.get(vertical_component) == road_agent.direction
                horizontal_opposite = opposite_directions.get(horizontal_component) == road_agent.direction

                # Si cualquiera de las componentes va en sentido contrario, RECHAZAR
                if vertical_opposite or horizontal_opposite:
                    return False

                # Si la componente vertical coincide con el Road, PERMITIR
                if vertical_component == road_agent.direction:
                    return True

                # Si la componente horizontal coincide con el Road, PERMITIR
                if horizontal_component == road_agent.direction:
                    return True

                # Si llegamos aquí, el movimiento es perpendicular al Road (giro con cambio de carril)
                # Esto se permite (por ejemplo, Road "Up" y movimiento "DownRight" hacia una calle perpendicular)
                return True

            # MOVIMIENTOS ORTOGONALES
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
        # Si está en estado de crash (chocado por un Borrachito), manejar el timer
        if self.crashed:
            self.crash_timer += 1
            if self.crash_timer >= 10:
                # Después de 10 steps, regresar a posición original
        
                self.move_to(self.original_position)
                self.crashed = False
                self.crash_timer = 0
                self.path = None  # Recalcular ruta
            return

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

        # Calculate path if needed
        if self.path is None:
            print(f"[UNIT {self.unique_id}] Computing route from {current_coord}")
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

        # Recalculate if blocked
        if self.stuck_counter >= 3:
            print(f"[UNIT {self.unique_id}] Blocked at {self.cell.coordinate}, recalc...")
            # Recalculate avoiding other units
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

        # Check if next cell is target
        is_next_destination = (next_cell.coordinate == self.destination.coordinate)
        if is_next_destination:
            print(f"[UNIT {self.unique_id}] Next is target {next_cell.coordinate}")

        # SEGURIDAD 1: Verificar que el movimiento sea válido (ortogonal o diagonal)
        current_x, current_y = self.cell.coordinate
        next_x, next_y = next_cell.coordinate
        dx = abs(next_x - current_x)
        dy = abs(next_y - current_y)

        # Movimientos válidos:
        # - Ortogonal: dx + dy == 1 (adelante en el carril)
        # - Diagonal: dx + dy == 2 y dx == 1 y dy == 1 (cambio de carril)
        is_orthogonal = (dx + dy == 1)
        is_diagonal = (dx + dy == 2 and dx == 1 and dy == 1)

        if not (is_orthogonal or is_diagonal):
            print(f"[UNIT {self.unique_id}] Invalid movement from {self.cell.coordinate} to {next_cell.coordinate}")
            # Recalcular ruta ya que algo salió mal
            self.path = None
            return

        # SEGURIDAD 2: Verificar dirección del movimiento
        movement_direction = self.get_direction(self.cell, next_cell)
        if movement_direction is None:
            print(f"[UNIT {self.unique_id}] Invalid dir from {self.cell.coordinate}")
            # Recalculate path
            self.path = None
            return

        # Verificar que el movimiento sigue siendo válido según las reglas de tráfico
        is_walkable = self.is_walkable(next_cell, movement_direction, self.destination, from_cell=self.cell)



        if not is_walkable:
            print(f"[UNIT {self.unique_id}] Invalid move from {self.cell.coordinate} (dir: {movement_direction})")
            if is_next_destination:
                print(f"[UNIT {self.unique_id}] Target unreachable")
            # Path invalid, recalculate
            self.path = None
            return

        # Verificar si hay semáforo en la siguiente celda
        traffic_light = None
        for agent in next_cell.agents:
            if isinstance(agent, Traffic_Light):
                traffic_light = agent
                break

        # Wait for traffic light
        if traffic_light and not traffic_light.state:
            if self.stuck_counter % 10 == 0:
                print(f"[UNIT {self.unique_id}] Waiting at {next_cell.coordinate}")
            self.stuck_counter += 1
            return

        # Check for other units
        has_car = any(isinstance(agent, Car) for agent in next_cell.agents)
        if has_car:
            if is_next_destination:
                print(f"[UNIT {self.unique_id}] Target occupied {next_cell.coordinate}")
            if self.stuck_counter % 10 == 0:
                print(f"[UNIT {self.unique_id}] Waiting at {next_cell.coordinate} (blocked {self.stuck_counter+1})")
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

class Borrachito(Car):
    """
    Borrachito agent. A drunk driver that doesn't respect traffic lights and can crash into other cars.
    """
    def __init__(self, model, cell):
        """
        Creates a new Borrachito agent.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model, cell)
        self.crashed = False
        self.crash_timer = 0
        self.original_position = cell
        self.crash_partner = None  # El otro coche con el que chocó

        print(f"[SPECIAL {self.unique_id}] Init at {self.cell.coordinate}")

    def move(self):
        """
        Mueve el Borrachito. No respeta semáforos y puede chocar con otros coches.
        """
        # Si está en estado de crash, manejar el timer
        if self.crashed:
            self.crash_timer += 1
            if self.crash_timer >= 10:
                # Después de 10 steps, regresar a posición original
                print(f"[SPECIAL {self.unique_id}] Returning to {self.original_position.coordinate}")
                self.move_to(self.original_position)
                self.crashed = False
                self.crash_timer = 0
                self.path = None  # Recalcular ruta
                self.crash_partner = None
            return

        # PRIMERO: Verificar si ya estamos en el destino
        current_coord = self.cell.coordinate
        dest_coord = self.destination.coordinate

        if current_coord == dest_coord:
            self.model.cars_arrived += 1
            if self.cell is not None:
                self.cell.remove_agent(self)
            self.model.agents.remove(self)
            return

        # Calculate path if needed
        if self.path is None:
            print(f"[SPECIAL {self.unique_id}] Computing route from {current_coord}")
            self.path = self.aStar()
            if self.path is None:
                return
            self.path_index = 0

        # Si ya llegamos al final de la ruta
        if self.path_index >= len(self.path) - 1:
            if self.path[-1].coordinate == self.destination.coordinate:
                if self.cell.coordinate == self.destination.coordinate:
                    return
            else:
                self.path = None
                return

        # Recalculate if blocked
        if self.stuck_counter >= 3:
            print(f"[SPECIAL {self.unique_id}] Blocked at {self.cell.coordinate}, recalc...")
            self.path = self.aStar(avoid_cars=True)
            if self.path is None:
                self.path = self.aStar(avoid_cars=False)
                if self.path is None:
                    return
            self.path_index = 0
            self.stuck_counter = 0

        # Siguiente celda en la ruta
        next_cell = self.path[self.path_index + 1]

        # SEGURIDAD: Verificar que el movimiento sea válido (ortogonal o diagonal)
        current_x, current_y = self.cell.coordinate
        next_x, next_y = next_cell.coordinate
        dx = abs(next_x - current_x)
        dy = abs(next_y - current_y)

        # Movimientos válidos:
        # - Ortogonal: dx + dy == 1 (adelante en el carril)
        # - Diagonal: dx + dy == 2 y dx == 1 y dy == 1 (cambio de carril)
        is_orthogonal = (dx + dy == 1)
        is_diagonal = (dx + dy == 2 and dx == 1 and dy == 1)

        if not (is_orthogonal or is_diagonal):
            print(f"[SPECIAL {self.unique_id}] Invalid movement from {self.cell.coordinate} to {next_cell.coordinate}")
            self.path = None
            return

        # SEGURIDAD: Verificar dirección del movimiento
        movement_direction = self.get_direction(self.cell, next_cell)
        if movement_direction is None:
            self.path = None
            return

        # Verificar que el movimiento sigue siendo válido
        is_walkable = self.is_walkable(next_cell, movement_direction, self.destination, from_cell=self.cell)

        if not is_walkable:
            self.path = None
            return

        # BORRACHITO NO RESPETA SEMÁFOROS - Comentamos esta sección
        # El borrachito ignora los semáforos en rojo

        # Verificar si hay otro coche en la siguiente celda
        other_car = None
        for agent in next_cell.agents:
            if isinstance(agent, (Car, Borrachito)) and agent != self:
                other_car = agent
                break

        if other_car:
            # 30% collision probability
            crash_chance = random.random()
            if crash_chance < 0.3:
                print(f"[SPECIAL {self.unique_id}] Collision with unit {other_car.unique_id} at {next_cell.coordinate}")
                # Mark both units as crashed
                self.crashed = True
                self.crash_timer = 0
                self.original_position = self.cell

                # Marcar el otro coche como chocado también
                if isinstance(other_car, Borrachito):
                    other_car.crashed = True
                    other_car.crash_timer = 0
                    other_car.original_position = other_car.cell
                else:
                    # Si es un Car normal, agregar atributos de crash
                    other_car.crashed = True
                    other_car.crash_timer = 0
                    other_car.original_position = other_car.cell

                return
            else:
                # No collision, wait
                if self.stuck_counter % 10 == 0:
                    print(f"[SPECIAL {self.unique_id}] Waiting at {next_cell.coordinate}")
                self.stuck_counter += 1
                return

        # Moverse a la siguiente celda
        self.move_to(next_cell)
        self.path_index += 1
        self.stuck_counter = 0
