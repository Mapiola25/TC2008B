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

        # IMPORTANTE: Limpiar la lista global de destinos al reiniciar el modelo
        # Esto evita que se acumulen destinos de modelos anteriores
        global destinations
        destinations.clear()
        print("[MODEL] Target list cleared")

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

        # VALIDACIÓN FINAL: Verificar que se cargaron destinos
        if not destinations:
            raise RuntimeError(f"Error crítico: El modelo se inicializó sin destinos. Revise el archivo de mapa.")

        print(f"[MODEL] Init OK: {len(destinations)} targets")

        # Verificar spawn points y sus Roads
        spawn_locations = [(0,0), (23, 0), (23, 24), (0, 24)]
        for spawn_loc in spawn_locations:
            cell = self.grid[spawn_loc]
            road_agents = [agent for agent in cell.agents if isinstance(agent, Road)]
            if road_agents:
                print(f"[MODEL] Point {spawn_loc} has path: {road_agents[0].direction}")
            else:
                print(f"[MODEL] Point {spawn_loc} path missing")

    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.current_step += 1

        # Show stats every 20 steps
        if self.current_step % 20 == 0:
            active_cars = sum(1 for agent in self.agents if isinstance(agent, (Car, Borrachito)))
            print(f"\n[STATS {self.current_step}] Active: {active_cars} | Total: {self.cars_spawned} | Done: {self.cars_arrived}")
            if self.cars_spawned > 0:
                print(f"[STATS] Rate: {(self.cars_arrived/self.cars_spawned*100):.1f}%\n")


        # Spawn new cars at specific locations (corners of the map)
        spawn_locations = [(0,0), (23, 0), (23, 24), (0, 24)]

        # Si el step coincide con el numero de n steps por spawn de coche
        if self.current_step % self.car_spawn_rate == 0:
            # Validate targets available
            if not destinations:
                print(f"[WARN] Spawn blocked: no targets")
                return

            # Si el modo borrachito está activado, spawnear 1 Borrachito y 3 Cars normales
            if self.borrachito_mode:
                # Elegir una ubicación aleatoria para el Borrachito
                import random
                borrachito_location = random.choice(spawn_locations)

                # Iterar por todas las ubicaciones
                for location in spawn_locations:
                    # Verificar si hay un coche en ESTA location específica
                    has_car_here = any(isinstance(agent, (Car, Borrachito)) for agent in self.grid[location].agents)

                    # Solo spawnear si NO hay un coche en esta location
                    if not has_car_here:
                        try:
                            cell = self.grid[location]

                            # Spawn special or normal agent
                            if location == borrachito_location:
                                agent = Borrachito(self, cell)
                                self.cars_spawned += 1
                                print(f"[SPAWN] Special unit #{self.cars_spawned} at {location}")
                            else:
                                # Spawn normal unit at other locations
                                agent = Car(self, cell)
                                self.cars_spawned += 1
                                print(f"[SPAWN] Unit #{self.cars_spawned} at {location}")
                        except Exception as e:
                            print(f"[ERR] Spawn failed at {location}: {e}")
                    else:
                        print(f"[SPAWN] Skip {location}: occupied")
            else:
                # Modo normal: spawnear coches en todas las ubicaciones
                for location in spawn_locations:
                    # Verificar si hay un coche en ESTA location específica
                    has_car_here = any(isinstance(agent, (Car, Borrachito)) for agent in self.grid[location].agents)

                    # Solo spawnear si NO hay un coche en esta location
                    if not has_car_here:
                        try:
                            cell = self.grid[location]
                            agent = Car(self, cell)
                            self.cars_spawned += 1
                            print(f"[SPAWN] Unit #{self.cars_spawned} at {location}")
                        except Exception as e:
                            print(f"[ERR] Spawn failed at {location}: {e}")
                    else:
                        print(f"[SPAWN] Skip {location}: occupied")
