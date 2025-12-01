from mesa.discrete_space import CellAgent, FixedAgent
import random
from collections import Counter

destinations = []

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
        self.destination = random.choice(destinations)
        self.cell = cell

    def aStar():
        pass

    def move(self):
        # print("Vecinos: ", random.choice(neighbors))
        # print("Current coordinate: ", self.cell.coordinate)
        # print("Destination of cell", self.destination)
        # print(random.choice(neighbors))
        neighbors = list(self.cell.neighborhood)
        next_move = None
        current_cell_agent = [type(agent).__name__ for agent in self.cell.agents]


        print(current_cell_agent)


        for n in neighbors:
            # Buscar si hay Road y Traffic_Light en la celda vecina
            road_agent = None
            traffic_light = None
            has_car = False

            for agent in n.agents:
                print("Agente en: ", n.coordinate, "Agentes ", agent)
                if isinstance(agent, Car):
                    has_car = True
                    break
                if isinstance(agent, Road):
                    road_agent = agent
                elif isinstance(agent, Traffic_Light):
                    traffic_light = agent

            # Si hay un coche, saltar esta celda vecina
            if has_car:
                continue

            if traffic_light and traffic_light.state == False:
                continue

            # Solo procesar si hay un Road (con o sin semáforo)
            if road_agent:
                # Calcular dirección del movimiento
                dx = n.coordinate[0] - self.cell.coordinate[0]
                dy = n.coordinate[1] - self.cell.coordinate[1]

                # Verificar si el movimiento coincide con la dirección del Road
                direction_matches = False
                if road_agent.direction == "Right" and dx > 0 and dy == 0:
                    direction_matches = True
                elif road_agent.direction == "Left" and dx < 0 and dy == 0:
                    direction_matches = True
                elif road_agent.direction == "Up" and dy > 0 and dx == 0:
                    direction_matches = True
                elif road_agent.direction == "Down" and dy < 0 and dx == 0:
                    direction_matches = True

                # Si la dirección es correcta, verificar semáforo
                if direction_matches:
                    # Si hay semáforo, solo mover si está en verde (state = True)
                    if traffic_light:
                        if traffic_light.state:  # Verde
                            next_move = n
                            print(f"Semáforo en verde en {n.coordinate}, moviendo")
                            break
                        else:  # Rojo
                            print(f"Semáforo en rojo en {n.coordinate}, esperando")
                            # No asignar next_move, el coche espera
                    else:
                        # No hay semáforo, mover libremente
                        next_move = n
                        break

            if next_move:
                break

        # print(directions)
        # contador = Counter(directions.values())
        # print(contador)
        # mas_comun = contador.most_common(1)
        # print(mas_comun)

        if next_move:
            self.move_to(next_move)

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
