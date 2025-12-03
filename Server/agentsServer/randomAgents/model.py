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
                    has_car_here = any(isinstance(agent, (Car, Borrachito)) for agent in self.grid[location].agents)

                    if not has_car_here:
                        try:
                            cell = self.grid[location]

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
                    has_car_here = any(isinstance(agent, (Car, Borrachito)) for agent in self.grid[location].agents)

                    if not has_car_here:
                        try:
                            cell = self.grid[location]
                            agent = Car(self, cell)
                            self.cars_spawned += 1
                        except:
                            pass
