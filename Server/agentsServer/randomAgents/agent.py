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

        # Validation
        if not destinations:
            raise ValueError("Initialization failed")

        self.destination = random.choice(destinations)
        self.cell = cell
        self.path = None
        self.path_index = 0
        self.stuck_counter = 0

        # State tracking
        self.crashed = False
        self.crash_timer = 0
        self.original_position = cell

        # Lane change attributes
        self.lane_change_state = None
        self.lane_change_progress = 0
        self.target_lane = None

        # Movement attributes
        self.speed = 1
        self.max_speed = 1
        self.steps_until_move = 0

    def get_orthogonal_neighbors(self, cell):
        """
        Gets neighboring cells for pathfinding.

        Args:
            cell: Source cell

        Returns:
            List[Cell]: List of adjacent cells
        """
        valid_neighbors = []
        current_x, current_y = cell.coordinate

        # Adjacent cells
        orthogonal_coords = [
            (current_x + 1, current_y),
            (current_x - 1, current_y),
            (current_x, current_y + 1),
            (current_x, current_y - 1),
        ]

        # Diagonal cells
        diagonal_coords = [
            (current_x + 1, current_y + 1),
            (current_x - 1, current_y + 1),
            (current_x + 1, current_y - 1),
            (current_x - 1, current_y - 1),
        ]

        all_valid_coords = orthogonal_coords + diagonal_coords

        for neighbor in cell.neighborhood:
            if neighbor.coordinate in all_valid_coords:
                valid_neighbors.append(neighbor)

        return valid_neighbors

    def reconstruct_path(self, parent_map, current_cell):
        """
        Reconstructs path from start to destination.

        Args:
            parent_map: Parent mapping
            current_cell: Final cell

        Returns:
            List[Cell]: Complete path
        """
        path = [current_cell]
        current_coord = current_cell.coordinate

        while current_coord in parent_map:
            current_cell = parent_map[current_coord]
            path.append(current_cell)
            current_coord = current_cell.coordinate

        path.reverse()
        return path

    def get_cell_at(self, x, y):
        """
        Gets cell at specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Cell: Cell at coordinates, or None
        """
        try:
            for cell in self.model.grid.all_cells:
                if cell.coordinate == (x, y):
                    return cell
            return None
        except:
            return None

    def get_cell_ahead(self, from_cell, direction, distance=1):
        """
        Gets cell ahead in specified direction.

        Args:
            from_cell: Source cell
            direction: Movement direction
            distance: Steps ahead

        Returns:
            Cell: Target cell, or None
        """
        x, y = from_cell.coordinate

        # Calculate offset
        if direction == "Up":
            y += distance
        elif direction == "Down":
            y -= distance
        elif direction == "Right":
            x += distance
        elif direction == "Left":
            x -= distance
        elif direction == "UpRight":
            x += distance
            y += distance
        elif direction == "UpLeft":
            x -= distance
            y += distance
        elif direction == "DownRight":
            x += distance
            y -= distance
        elif direction == "DownLeft":
            x -= distance
            y -= distance
        else:
            return None

        return self.get_cell_at(x, y)

    def get_cell_behind(self, from_cell, direction, distance=1):
        """
        Gets cell behind in specified direction.

        Args:
            from_cell: Source cell
            direction: Movement direction
            distance: Steps behind

        Returns:
            Cell: Target cell, or None
        """
        # Reverse direction
        opposite_directions = {
            "Up": "Down",
            "Down": "Up",
            "Left": "Right",
            "Right": "Left",
            "UpRight": "DownLeft",
            "UpLeft": "DownRight",
            "DownRight": "UpLeft",
            "DownLeft": "UpRight"
        }

        opposite_dir = opposite_directions.get(direction)
        if not opposite_dir:
            return None

        return self.get_cell_ahead(from_cell, opposite_dir, distance)

    def aStar(self, avoid_cars=False):
        """
        Pathfinding algorithm to find optimal route.

        Args:
            avoid_cars: Avoid cells with other agents

        Returns:
            List[Cell]: Optimal path, or None if no route
        """
        start = self.cell
        goal = self.destination

        # Check if already at destination
        if start.coordinate == goal.coordinate:
            return [start]

        # Initialize data structures
        open_set = []
        closed_set = set()

        g_score = {start.coordinate: 0}
        f_score = {start.coordinate: heuristic(start, goal)}
        parent_map = {}

        heapq.heappush(open_set, (f_score[start.coordinate], start.coordinate, start))

        explored_count = 0
        while open_set:
            result = heapq.heappop(open_set)
            current_f = result[0]
            current_coord = result[1]
            current_cell = result[2]

            explored_count += 1

            # Check if reached destination
            if current_cell.coordinate == goal.coordinate:
                path = self.reconstruct_path(parent_map, current_cell)
                return path

            closed_set.add(current_coord)

            neighbors_checked = 0
            neighbors_valid = 0
            all_neighbors = self.get_orthogonal_neighbors(current_cell)
            random.shuffle(all_neighbors)  # Aleatoriza orden para variar rutas

            for neighbor in all_neighbors:
                neighbor_coord = neighbor.coordinate
                neighbors_checked += 1

                if neighbor_coord in closed_set:
                    continue

                direction = self.get_direction(current_cell, neighbor)

                if direction is None:
                    continue

                is_first_move = (current_cell.coordinate == start.coordinate)

                if is_first_move:
                    walkable = self.is_walkable(neighbor, None, goal, allow_lane_change=True, check_cars=avoid_cars, from_cell=current_cell)
                    if not walkable:
                        continue
                else:
                    if not self.is_walkable(neighbor, direction, goal, allow_lane_change=True, check_cars=avoid_cars, from_cell=current_cell):
                        continue

                neighbors_valid += 1

                is_spawn_or_destination = current_cell.coordinate == start.coordinate or any(
                    isinstance(agent, Destination) for agent in current_cell.agents
                )

                base_cost = 1

                # Spawning inteligente: evaluar congestión en el primer movimiento
                if is_first_move and current_cell.coordinate == start.coordinate:
                    # Obtener la dirección del carril vecino
                    road_in_neighbor = None
                    for agent in neighbor.agents:
                        if isinstance(agent, Road):
                            road_in_neighbor = agent
                            break

                    if road_in_neighbor:
                        # Calcular congestión en esa dirección
                        congestion = self.calculate_lane_congestion(neighbor, road_in_neighbor.direction)
                        # Añadir costo proporcional a la congestión
                        base_cost += congestion * 0.5

                if not is_spawn_or_destination and self.is_lane_change(current_cell, neighbor):
                    base_cost += 1

                tentative_g = g_score[current_coord] + base_cost

                if neighbor_coord not in g_score or tentative_g < g_score[neighbor_coord]:
                    parent_map[neighbor_coord] = current_cell
                    g_score[neighbor_coord] = tentative_g
                    h = heuristic(neighbor, goal)
                    # Añadir factor aleatorio para romper empates
                    # En spawn points, la congestión ya provee variación, así que usamos factor menor
                    if is_spawn_or_destination:
                        random_factor = random.uniform(0, 0.3)  # Factor pequeño, la congestión decide
                    else:
                        random_factor = random.uniform(0, 0.5)  # Factor moderado en ruta
                    f_score[neighbor_coord] = tentative_g + h + random_factor

                    if neighbor_coord not in [item[1] for item in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor_coord], neighbor_coord, neighbor))

        return None

    def get_direction(self, from_cell, to_cell):
        """
        Calculates movement direction between cells.

        Args:
            from_cell: Source cell
            to_cell: Target cell

        Returns:
            str: Direction string or None
        """
        dx = to_cell.coordinate[0] - from_cell.coordinate[0]
        dy = to_cell.coordinate[1] - from_cell.coordinate[1]

        # Orthogonal movements
        if abs(dx) + abs(dy) == 1:
            if dx > 0 and dy == 0:
                return "Right"
            elif dx < 0 and dy == 0:
                return "Left"
            elif dy > 0 and dx == 0:
                return "Up"
            elif dy < 0 and dx == 0:
                return "Down"

        # Diagonal movements
        elif abs(dx) + abs(dy) == 2 and abs(dx) == 1 and abs(dy) == 1:
            if dx > 0 and dy > 0:
                return "UpRight"
            elif dx < 0 and dy > 0:
                return "UpLeft"
            elif dx > 0 and dy < 0:
                return "DownRight"
            elif dx < 0 and dy < 0:
                return "DownLeft"

        return None

    def look_ahead(self, steps=5):
        """
        Checks ahead for obstacles.

        Args:
            steps: Distance to check

        Returns:
            tuple: (is_blocked, distance, type)
        """
        if not self.path or self.path_index >= len(self.path) - 1:
            return False, None, None

        max_lookahead = min(steps, len(self.path) - self.path_index - 1)

        for i in range(1, max_lookahead + 1):
            future_cell = self.path[self.path_index + i]

            has_car = any(isinstance(agent, Car) for agent in future_cell.agents)
            if has_car:
                return True, i, "car"

            for agent in future_cell.agents:
                if isinstance(agent, Traffic_Light) and not agent.state:
                    return True, i, "traffic_light"

        return False, None, None

    def calculate_lane_congestion(self, cell, direction, lookahead=8):
        """
        Calcula el nivel de congestión en un carril mirando hacia adelante.

        Args:
            cell: Celda inicial
            direction: Dirección a revisar
            lookahead: Número de celdas a revisar hacia adelante

        Returns:
            int: Número de coches encontrados (mayor = más congestión)
        """
        congestion = 0

        for i in range(1, lookahead + 1):
            next_cell = self.get_cell_ahead(cell, direction, i)
            if not next_cell:
                break

            # Contar coches en esta celda
            car_count = sum(1 for agent in next_cell.agents if isinstance(agent, (Car, Borrachito)))
            congestion += car_count

            # Penalizar semáforos en rojo
            for agent in next_cell.agents:
                if isinstance(agent, Traffic_Light) and not agent.state:
                    congestion += 2  # Semáforo rojo cuenta como 2 coches

        return congestion

    def is_lane_change(self, from_cell, to_cell):
        """
        Detects if movement is a lane change.

        Args:
            from_cell: Source cell
            to_cell: Target cell

        Returns:
            bool: True if lane change
        """
        movement_direction = self.get_direction(from_cell, to_cell)

        if movement_direction is None:
            return False

        if movement_direction in ["UpRight", "UpLeft", "DownRight", "DownLeft"]:
            return True

        road_agent = None
        for agent in from_cell.agents:
            if isinstance(agent, Road):
                road_agent = agent
                break

        if not road_agent:
            return False

        if movement_direction in ["Left", "Right"]:
            if road_agent.direction in ["Up", "Down"]:
                return True
        elif movement_direction in ["Up", "Down"]:
            if road_agent.direction in ["Left", "Right"]:
                return True

        return False

    def is_safe_to_change_lane(self, target_cell, direction):
        """
        Checks if lane change is safe.

        Args:
            target_cell: Target cell
            direction: Movement direction

        Returns:
            bool: True if safe
        """
        has_car = any(isinstance(agent, Car) for agent in target_cell.agents)
        if has_car:
            return False

        for i in range(1, 2):
            future_cell = self.get_cell_ahead(target_cell, direction, i)
            if future_cell:
                has_car_ahead = any(isinstance(agent, Car) for agent in future_cell.agents)
                if has_car_ahead:
                    return False

        for i in range(1, 2):
            behind_cell = self.get_cell_behind(target_cell, direction, i)
            if behind_cell:
                for agent in behind_cell.agents:
                    if isinstance(agent, Car):
                        return False

        return True

    def try_lane_change(self):
        """
        Finds alternative lane if available.

        Returns:
            Cell: Alternative cell, or None
        """
        if not self.path or self.path_index >= len(self.path) - 1:
            return None

        current_cell = self.cell
        next_in_path = self.path[self.path_index + 1]

        movement_direction = self.get_direction(current_cell, next_in_path)
        if not movement_direction:
            return None

        current_x, current_y = current_cell.coordinate

        adjacent_coords = [
            (current_x + 1, current_y),
            (current_x - 1, current_y),
        ]

        for adj_x, adj_y in adjacent_coords:
            adjacent_cell = self.get_cell_at(adj_x, adj_y)

            if not adjacent_cell:
                continue

            has_road = any(isinstance(agent, Road) for agent in adjacent_cell.agents)
            if not has_road:
                continue

            has_obstacle = any(isinstance(agent, Obstacle) for agent in adjacent_cell.agents)
            if has_obstacle:
                continue

            if self.is_safe_to_change_lane(adjacent_cell, movement_direction):
                direction_to_adjacent = self.get_direction(current_cell, adjacent_cell)
                if self.is_walkable(adjacent_cell, direction_to_adjacent, self.destination, from_cell=current_cell):
                    return adjacent_cell

        return None

    def is_walkable(self, cell, direction_from_parent=None, goal=None, allow_lane_change=True, check_cars=False, from_cell=None):
        """
        Checks if cell is accessible.

        Args:
            cell: Cell to check
            direction_from_parent: Direction from parent
            goal: Destination cell
            allow_lane_change: Allow lateral movements
            check_cars: Avoid cells with agents
            from_cell: Source cell

        Returns:
            bool: True if accessible
        """
        if goal and cell.coordinate == goal.coordinate:
            has_obstacle = any(isinstance(agent, Obstacle) for agent in cell.agents)
            return not has_obstacle

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

        if has_obstacle:
            return False

        if has_car and check_cars:
            return False

        # Solo permitir pasar por destinos si es el destino propio del coche
        if has_destination:
            if goal and cell.coordinate == goal.coordinate:
                return True
            else:
                # Es un destino pero no es el nuestro - tratarlo como obstáculo
                return False

        if not road_agent:
            return False

        if direction_from_parent:
            if from_cell:
                from_has_road = any(isinstance(agent, Road) for agent in from_cell.agents)
                from_has_destination = any(isinstance(agent, Destination) for agent in from_cell.agents)

                spawn_points = [(0, 0), (35, 0), (0, 34), (35, 34)]
                is_spawn_point = from_cell.coordinate in spawn_points

                if is_spawn_point or from_has_destination or not from_has_road:
                    return True


            if direction_from_parent in ["UpRight", "UpLeft", "DownRight", "DownLeft"]:
                vertical_component = "Up" if "Up" in direction_from_parent else "Down"
                horizontal_component = "Right" if "Right" in direction_from_parent else "Left"

                opposite_directions = {
                    "Up": "Down",
                    "Down": "Up",
                    "Left": "Right",
                    "Right": "Left"
                }

                vertical_opposite = opposite_directions.get(vertical_component) == road_agent.direction
                horizontal_opposite = opposite_directions.get(horizontal_component) == road_agent.direction

                if vertical_opposite or horizontal_opposite:
                    return False

                if vertical_component == road_agent.direction:
                    return True

                if horizontal_component == road_agent.direction:
                    return True

                return True

            opposite_directions = {
                "Up": "Down",
                "Down": "Up",
                "Left": "Right",
                "Right": "Left"
            }

            if opposite_directions.get(direction_from_parent) == road_agent.direction:
                return False

            if road_agent.direction == direction_from_parent:
                return True

            return True

        return True

    def move(self):
        """
        Moves agent along calculated path.
        """
        if self.crashed:
            self.crash_timer += 1
            if self.crash_timer >= 10:
                self.move_to(self.original_position)
                self.crashed = False
                self.crash_timer = 0
                self.path = None
            return

        current_coord = self.cell.coordinate
        dest_coord = self.destination.coordinate

        if current_coord == dest_coord:
            self.model.cars_arrived += 1

            if self.cell is not None:
                self.cell.remove_agent(self)

            self.model.agents.remove(self)
            return

        if self.path is None:
            self.path = self.aStar()
            if self.path is None:
                return
            self.path_index = 0

        if self.path_index >= len(self.path) - 1:
            if self.path[-1].coordinate == self.destination.coordinate:
                if self.cell.coordinate == self.destination.coordinate:
                    return
            else:
                self.path = None
                return

        # Recalculate if blocked
        next_cell = self.path[self.path_index + 1]

        traffic_light_blocking = None
        for agent in next_cell.agents:
            if isinstance(agent, Traffic_Light):
                traffic_light_blocking = agent
                break

        if self.stuck_counter >= 2:
            if not (traffic_light_blocking and not traffic_light_blocking.state):
                alternative_lane = self.try_lane_change()
                if alternative_lane:
                    self.move_to(alternative_lane)
                    self.path = None
                    self.stuck_counter = 0
                    return

                self.path = self.aStar(avoid_cars=True)
                if self.path is None:
                    self.path = self.aStar(avoid_cars=False)
                    if self.path is None:
                        return
                self.path_index = 0
                self.stuck_counter = 0

        is_next_destination = (next_cell.coordinate == self.destination.coordinate)

        current_x, current_y = self.cell.coordinate
        next_x, next_y = next_cell.coordinate
        dx = abs(next_x - current_x)
        dy = abs(next_y - current_y)

        is_orthogonal = (dx + dy == 1)
        is_diagonal = (dx + dy == 2 and dx == 1 and dy == 1)

        if not (is_orthogonal or is_diagonal):
            self.path = None
            return

        movement_direction = self.get_direction(self.cell, next_cell)
        if movement_direction is None:
            self.path = None
            return

        is_walkable = self.is_walkable(next_cell, movement_direction, self.destination, from_cell=self.cell)

        if not is_walkable:
            self.path = None
            return

        if traffic_light_blocking and not traffic_light_blocking.state:
            self.stuck_counter += 1
            return

        has_car = any(isinstance(agent, Car) for agent in next_cell.agents)
        if has_car:
            self.stuck_counter += 1
            return

        # Safety distance check
        future_cell = self.get_cell_ahead(next_cell, movement_direction, 1)
        if future_cell:
            has_car_ahead = any(isinstance(agent, Car) for agent in future_cell.agents)
            if has_car_ahead:
                if random.random() < 0.3:
                    self.stuck_counter += 1
                    return

        self.move_to(next_cell)

        self.path_index += 1
        self.stuck_counter = 0

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
    Special agent with different behavior.
    """
    def __init__(self, model, cell):
        """
        Creates a new special agent.
        Args:
            model: Model reference for the agent
            cell: The initial position of the agent
        """
        super().__init__(model, cell)
        self.crashed = False
        self.crash_timer = 0
        self.original_position = cell
        self.crash_partner = None

    def move(self):
        """
        Moves agent with alternate behavior - MODO BORRACHITO EXAGERADO.
        """
        if self.crashed:
            self.crash_timer += 1
            if self.crash_timer >= 10:
                self.move_to(self.original_position)
                self.crashed = False
                self.crash_timer = 0
                self.path = None
                self.crash_partner = None
            return

        current_coord = self.cell.coordinate
        dest_coord = self.destination.coordinate

        if current_coord == dest_coord:
            self.model.cars_arrived += 1
            if self.cell is not None:
                self.cell.remove_agent(self)
            self.model.agents.remove(self)
            return

        if self.path is None:
            self.path = self.aStar()
            if self.path is None:
                return
            self.path_index = 0

        if self.path_index >= len(self.path) - 1:
            if self.path[-1].coordinate == self.destination.coordinate:
                if self.cell.coordinate == self.destination.coordinate:
                    return
            else:
                self.path = None
                return

        if self.stuck_counter >= 3:
            self.path = self.aStar(avoid_cars=True)
            if self.path is None:
                self.path = self.aStar(avoid_cars=False)
                if self.path is None:
                    return
            self.path_index = 0
            self.stuck_counter = 0

        # MODO BORRACHITO: 80% de probabilidad de movimiento errático diagonal
        borrachito_mode = random.random() < 0.8

        if borrachito_mode:
            # Movimientos diagonales aleatorios en todas direcciones
            current_x, current_y = self.cell.coordinate

            # Todas las direcciones diagonales posibles + algunas ortogonales
            diagonal_offsets = [
                (1, 1),   # UpRight
                (-1, 1),  # UpLeft
                (1, -1),  # DownRight
                (-1, -1), # DownLeft
                (2, 1),   # Diagonal exagerado
                (-2, 1),  # Diagonal exagerado
                (1, 2),   # Diagonal exagerado
                (-1, 2),  # Diagonal exagerado
                (2, -1),  # Diagonal exagerado
                (-2, -1), # Diagonal exagerado
                (1, -2),  # Diagonal exagerado
                (-1, -2), # Diagonal exagerado
            ]

            # Barajar para movimientos impredecibles
            random.shuffle(diagonal_offsets)

            moved = False
            for dx, dy in diagonal_offsets:
                target_x = current_x + dx
                target_y = current_y + dy
                target_cell = self.get_cell_at(target_x, target_y)

                if target_cell:
                    # Verificar si tiene camino (road)
                    has_road = any(isinstance(agent, Road) for agent in target_cell.agents)
                    has_obstacle = any(isinstance(agent, Obstacle) for agent in target_cell.agents)

                    if has_road and not has_obstacle:
                        # Intentar moverse, ignorando semáforos
                        other_car = None
                        for agent in target_cell.agents:
                            if isinstance(agent, (Car, Borrachito)) and agent != self:
                                other_car = agent
                                break

                        if other_car:
                            # Mayor probabilidad de choque en modo borrachito
                            crash_chance = random.random()
                            if crash_chance < 0.5:  # 50% de probabilidad de choque
                                self.crashed = True
                                self.crash_timer = 0
                                self.original_position = self.cell

                                other_car.crashed = True
                                other_car.crash_timer = 0
                                other_car.original_position = other_car.cell
                                moved = True
                                break
                            else:
                                # Intenta otra dirección
                                continue
                        else:
                            # Moverse a la celda diagonal
                            self.move_to(target_cell)
                            moved = True
                            break

            if moved:
                # Resetear el path ocasionalmente para más caos
                if random.random() < 0.4:
                    self.path = None
                self.stuck_counter = 0
                return

        # Si no se movió en modo borrachito, usar el comportamiento normal pero más agresivo
        next_cell = self.path[self.path_index + 1]

        current_x, current_y = self.cell.coordinate
        next_x, next_y = next_cell.coordinate
        dx = abs(next_x - current_x)
        dy = abs(next_y - current_y)

        is_orthogonal = (dx + dy == 1)
        is_diagonal = (dx + dy == 2 and dx == 1 and dy == 1)

        if not (is_orthogonal or is_diagonal):
            self.path = None
            return

        movement_direction = self.get_direction(self.cell, next_cell)
        if movement_direction is None:
            self.path = None
            return

        is_walkable = self.is_walkable(next_cell, movement_direction, self.destination, from_cell=self.cell)

        if not is_walkable:
            self.path = None
            return

        # Special behavior: ignores traffic lights

        other_car = None
        for agent in next_cell.agents:
            if isinstance(agent, (Car, Borrachito)) and agent != self:
                other_car = agent
                break

        if other_car:
            crash_chance = random.random()
            if crash_chance < 0.5:  # Mayor probabilidad de choque
                self.crashed = True
                self.crash_timer = 0
                self.original_position = self.cell

                if isinstance(other_car, Borrachito):
                    other_car.crashed = True
                    other_car.crash_timer = 0
                    other_car.original_position = other_car.cell
                else:
                    other_car.crashed = True
                    other_car.crash_timer = 0
                    other_car.original_position = other_car.cell

                return
            else:
                self.stuck_counter += 1
                return

        self.move_to(next_cell)
        self.path_index += 1
        self.stuck_counter = 0
