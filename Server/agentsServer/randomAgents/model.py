from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Car, Traffic_Light, Destination, Obstacle, Road, Borrachito, destinations
import json
import os


class CityModel(Model):
    """
    Creates a model based on a city map.

    Args:
        N: Number of agents in the simulation
        seed: Random seed for the model
    """

    def __init__(self, N, seed=42, spawn_of_cars = 5):

        super().__init__(seed=seed)

        # Reset global state
        global destinations
        destinations.clear()

        # Load the map dictionary. The dictionary maps the characters in the map file to the corresponding agent.
        base_path = os.path.dirname(__file__)
        dataDictionary = json.load(open(os.path.join(base_path, "city_files/mapDictionary.json")))

        self.num_agents = N
        self.car_spawn_rate = spawn_of_cars
        self.current_step = 0
        self.cars_spawned = 0  # Contador de coches generados
        self.cars_arrived = 0  # Contador de coches que llegaron al destino
        self.borrachito_mode = False  # Modo borrachito desactivado por defecto

        # Load the map file. The map file is a text file where each character represents an agent.
        with open(os.path.join(base_path, "city_files/2025_base.txt")) as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0])
            self.height = len(lines)

            self.grid = OrthogonalMooreGrid(
                [self.width, self.height], capacity=100, torus=False
            )

            # Goes through each character in the map file and creates the corresponding agent.

            for r, row in enumerate(lines):
                for c, col in enumerate(row):

                    cell = self.grid[(c, self.height - r - 1)]

                    if col in ["v", "^", ">", "<"]:
                        agent = Road(self, cell, dataDictionary[col])

                    elif col in ["S", "s"]:
                        # Check adjacent cells
                        direction = "Left"

                        if r > 0 and lines[r-1][c] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r-1][c]]
                        elif r < len(lines)-1 and lines[r+1][c] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r+1][c]]
                        elif c > 0 and lines[r][c-1] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r][c-1]]
                        elif c < len(row)-1 and lines[r][c+1] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r][c+1]]

                        agent = Road(self, cell, direction)
                        agent = Traffic_Light(
                            self,
                            cell,
                            False if col == "S" else True,
                            int(dataDictionary[col]),
                        )



                    elif col == "#":
                        agent = Obstacle(self, cell)

                    elif col == "D":
                        agent = Destination(self, cell)




        self.running = True

        # Validate initialization
        if not destinations:
            raise RuntimeError("Initialization failed: missing required data")

    def get_cell_at(self, x, y):
        """
        Gets cell at specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Cell: Cell at coordinates, or None
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[(x, y)]
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

    def get_valid_spawn_cells(self, spawn_location):
        """
        Obtiene todas las celdas válidas alrededor de un spawn point.

        Args:
            spawn_location: Tupla (x, y) del spawn point

        Returns:
            List[Cell]: Lista de celdas válidas ordenadas por congestión
        """
        x, y = spawn_location
        valid_cells = []

        # Celdas adyacentes (ortogonales y diagonales)
        neighbors = [
            (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),  # Ortogonales
            (x + 1, y + 1), (x - 1, y + 1), (x + 1, y - 1), (x - 1, y - 1)  # Diagonales
        ]

        # Incluir también el spawn point mismo
        neighbors.insert(0, spawn_location)

        for nx, ny in neighbors:
            # Verificar que esté dentro de los límites
            if 0 <= nx < self.width and 0 <= ny < self.height:
                cell = self.grid[(nx, ny)]

                # Verificar que tenga Road
                has_road = any(isinstance(agent, Road) for agent in cell.agents)
                if not has_road:
                    continue

                # Verificar que NO tenga obstáculos
                has_obstacle = any(isinstance(agent, Obstacle) for agent in cell.agents)
                if has_obstacle:
                    continue

                # Verificar que NO tenga coches
                has_car = any(isinstance(agent, (Car, Borrachito)) for agent in cell.agents)
                if has_car:
                    continue

                # Obtener la dirección del Road para calcular congestión
                road_agent = None
                for agent in cell.agents:
                    if isinstance(agent, Road):
                        road_agent = agent
                        break

                if road_agent:
                    valid_cells.append((cell, road_agent.direction))

        # Ordenar por congestión (menor congestión primero)
        if valid_cells:
            cells_with_congestion = []
            for cell, direction in valid_cells:
                congestion = self.calculate_lane_congestion(cell, direction, lookahead=8)
                cells_with_congestion.append((cell, congestion))

            # Ordenar por congestión
            cells_with_congestion.sort(key=lambda x: x[1])
            return [cell for cell, _ in cells_with_congestion]

        return []

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.current_step += 1


        # Process spawn logic - Todas las 4 esquinas del mapa
        spawn_locations = [(0, 0), (35, 0), (0, 34), (35, 34)]

        # Check spawn timing
        if self.current_step % self.car_spawn_rate == 0:
            if not destinations:
                return

            # Special mode enabled
            if self.borrachito_mode:
                import random
                borrachito_location = random.choice(spawn_locations)

                for location in spawn_locations:
                    # Obtener todas las celdas válidas alrededor del spawn point
                    valid_cells = self.get_valid_spawn_cells(location)

                    if valid_cells:
                        try:
                            # Usar la celda menos congestionada
                            cell = valid_cells[0]

                            if location == borrachito_location:
                                agent = Borrachito(self, cell)
                                self.cars_spawned += 1
                            else:
                                agent = Car(self, cell)
                                self.cars_spawned += 1
                        except:
                            pass
            else:
                for location in spawn_locations:
                    # Obtener todas las celdas válidas alrededor del spawn point
                    valid_cells = self.get_valid_spawn_cells(location)

                    if valid_cells:
                        try:
                            # Usar la celda menos congestionada
                            cell = valid_cells[0]
                            agent = Car(self, cell)
                            self.cars_spawned += 1
                        except:
                            pass
