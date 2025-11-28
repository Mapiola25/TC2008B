from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import *
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

        # Load the map dictionary. The dictionary maps the characters in the map file to the corresponding agent.
        base_path = os.path.dirname(__file__)
        dataDictionary = json.load(open(os.path.join(base_path, "city_files/mapDictionary.json")))

        self.num_agents = N
        self.car_spawn_rate = spawn_of_cars
        self.current_step = 0

        # Load the map file. The map file is a text file where each character represents an agent.
        with open(os.path.join(base_path, "city_files/2022_base.txt")) as baseFile:
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
                        # Inferir dirección del semáforo mirando celdas adyacentes
                        direction = "Left"  # Default

                        # Revisar celda de arriba (r-1)
                        if r > 0 and lines[r-1][c] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r-1][c]]
                        # Revisar celda de abajo (r+1)
                        elif r < len(lines)-1 and lines[r+1][c] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r+1][c]]
                        # Revisar celda de izquierda (c-1)
                        elif c > 0 and lines[r][c-1] in ["v", "^", ">", "<"]:
                            direction = dataDictionary[lines[r][c-1]]
                        # Revisar celda de derecha (c+1)
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

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.current_step += 1
        

        # Spawn new cars at specific locations (corners of the map)
        spawn_locations = [(0,0), (23, 0), (23, 24), (0, 24)]
        has car = False
        # Logica para detectar si en las celdas de spawn ya hay coches
        for location in spawn_locations:
            for agent in self.grid[location].agents:
                if isinstance(agent, Car):
                    has_car = True 

        
        
        # Si el step coincide con el numero de n steps por spawn de coche
        if self.current_step % self.car_spawn_rate == 0:
            if has_car == False: # Si no hay un coche ahi esperando para salir
                for location in spawn_locations:
                    try:
                        cell = self.grid[location]
                        agent = Car(self, cell)
                        print(f"New car spawned at {location}")
                    except Exception as e:
                        print(f"Error spawning car at {location}: {e}")
