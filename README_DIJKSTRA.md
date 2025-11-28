# Implementación de Dijkstra para Navegación de Coches

## Análisis del Código Actual

### Estructura Existente (agent.py)

El sistema actual tiene los siguientes componentes:

- **Car** (agent.py:7-100): Agentes que se mueven siguiendo direcciones de calles
- **Road** (agent.py:158-172): Celdas navegables con dirección (Up, Down, Left, Right)
- **Traffic_Light** (agent.py:102-126): Semáforos que controlan el flujo
- **Destination** (agent.py:127-141): Puntos de destino para los coches
- **Obstacle** (agent.py:143-157): Obstáculos no navegables

### Problema Actual

El método `move()` (agent.py:25-94) actualmente:
- Solo sigue la dirección de la calle en la que está el coche
- No calcula rutas óptimas hacia el destino
- Puede llevar a los coches por caminos subóptimos o ciclos infinitos
- No hay planificación de ruta (pathfinding)

## Propuesta de Implementación: Algoritmo de Dijkstra

### Conceptos Clave

**Dijkstra** es un algoritmo de búsqueda de camino más corto que:
1. Encuentra el camino de menor costo desde un nodo inicial a todos los demás nodos
2. Garantiza el camino óptimo en grafos con pesos no negativos
3. Es más eficiente que A* cuando no hay heurística disponible

### Diseño de la Solución

#### 1. Construcción del Grafo

Crear un grafo dirigido donde:
- **Nodos**: Cada celda con un agente Road
- **Aristas**: Conexiones entre celdas adyacentes respetando la dirección del Road
- **Pesos**: Costo de moverse entre celdas (puede ser 1 o considerar semáforos)

```python
def build_graph(model):
    """
    Construye un grafo dirigido basado en las Roads del modelo.

    Returns:
        dict: {coordinate: [(neighbor_coord, weight), ...]}
    """
    graph = {}

    for cell in model.grid.all_cells:
        road = None
        for agent in cell.agents:
            if isinstance(agent, Road):
                road = agent
                break

        if not road:
            continue

        coord = cell.coordinate
        graph[coord] = []

        # Verificar vecinos según la dirección del Road
        for neighbor in cell.neighborhood:
            neighbor_road = None
            for agent in neighbor.agents:
                if isinstance(agent, Road):
                    neighbor_road = agent
                    break

            if not neighbor_road:
                continue

            # Calcular dirección del movimiento
            dx = neighbor.coordinate[0] - coord[0]
            dy = neighbor.coordinate[1] - coord[1]

            # Verificar si la dirección coincide
            can_move = False
            if road.direction == "Right" and dx > 0 and dy == 0:
                can_move = True
            elif road.direction == "Left" and dx < 0 and dy == 0:
                can_move = True
            elif road.direction == "Up" and dy > 0 and dx == 0:
                can_move = True
            elif road.direction == "Down" and dy < 0 and dx == 0:
                can_move = True

            if can_move:
                weight = 1  # Peso básico
                # Opcional: aumentar peso si hay semáforo rojo
                graph[coord].append((neighbor.coordinate, weight))

    return graph
```

#### 2. Implementación de Dijkstra

```python
import heapq

def dijkstra(graph, start, end):
    """
    Calcula el camino más corto usando Dijkstra.

    Args:
        graph: Grafo de adyacencias {coord: [(neighbor, weight), ...]}
        start: Coordenada inicial
        end: Coordenada destino

    Returns:
        list: Camino como lista de coordenadas [start, ..., end]
              o None si no hay camino
    """
    # Priority queue: (distancia, coordenada)
    pq = [(0, start)]

    # Distancias mínimas conocidas
    distances = {start: 0}

    # Para reconstruir el camino
    previous = {start: None}

    visited = set()

    while pq:
        current_dist, current = heapq.heappop(pq)

        if current in visited:
            continue

        visited.add(current)

        # Si llegamos al destino, reconstruir el camino
        if current == end:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1]  # Invertir para tener start -> end

        # Explorar vecinos
        if current not in graph:
            continue

        for neighbor, weight in graph[current]:
            distance = current_dist + weight

            if neighbor not in distances or distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current
                heapq.heappush(pq, (distance, neighbor))

    return None  # No hay camino
```

#### 3. Modificación de la Clase Car

```python
class Car(CellAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.destination = random.choice(destinations)
        self.cell = cell
        self.path = []  # Camino calculado
        self.path_index = 0  # Posición actual en el camino
        self.recalculate_path()

    def recalculate_path(self):
        """
        Calcula el camino óptimo al destino usando Dijkstra.
        """
        graph = build_graph(self.model)
        start = self.cell.coordinate
        end = self.destination.coordinate

        self.path = dijkstra(graph, start, end)
        self.path_index = 0

        if not self.path:
            print(f"No se encontró camino de {start} a {end}")

    def move(self):
        """
        Mueve el coche siguiendo el camino calculado.
        """
        # Si no hay camino o ya llegamos, no mover
        if not self.path or self.path_index >= len(self.path) - 1:
            return

        # Obtener la siguiente celda en el camino
        next_coord = self.path[self.path_index + 1]

        # Buscar la celda correspondiente
        next_cell = None
        for neighbor in self.cell.neighborhood:
            if neighbor.coordinate == next_coord:
                next_cell = neighbor
                break

        if not next_cell:
            # Si no se encuentra la celda, recalcular camino
            self.recalculate_path()
            return

        # Verificar semáforos
        can_move = True
        for agent in next_cell.agents:
            if isinstance(agent, Traffic_Light):
                if not agent.state:  # Rojo
                    can_move = False
                    break

        if can_move:
            self.move_to(next_cell)
            self.path_index += 1

            # Si llegamos al destino
            if self.cell.coordinate == self.destination.coordinate:
                print(f"Coche llegó al destino: {self.destination.coordinate}")
                # Opcional: asignar nuevo destino
                # self.destination = random.choice(destinations)
                # self.recalculate_path()

    def step(self):
        """
        Determina la nueva dirección y se mueve.
        """
        self.move()
```

#### 4. Optimizaciones Propuestas

##### a) Caché del Grafo

En lugar de reconstruir el grafo en cada llamada, construirlo una vez en el modelo:

```python
class CityModel:
    def __init__(self, ...):
        # ... inicialización existente ...
        self.graph = None

    def setup(self):
        # ... setup existente ...
        # Construir el grafo después de colocar todas las Roads
        self.graph = build_graph(self)
```

Luego modificar `recalculate_path()`:

```python
def recalculate_path(self):
    start = self.cell.coordinate
    end = self.destination.coordinate
    self.path = dijkstra(self.model.graph, start, end)
    self.path_index = 0
```

##### b) Recalculación Inteligente

Solo recalcular el camino cuando:
- Hay un obstáculo temporal (otro coche bloqueando)
- Un semáforo cambia el costo del grafo
- El coche se desvió del camino

```python
def needs_recalculation(self):
    """
    Determina si se necesita recalcular el camino.
    """
    # Si no hay camino
    if not self.path:
        return True

    # Si la posición actual no coincide con el camino
    if self.cell.coordinate != self.path[self.path_index]:
        return True

    # Si llegamos al destino
    if self.path_index >= len(self.path) - 1:
        return False

    return False
```

##### c) Consideración de Tráfico

Ajustar pesos del grafo según el tráfico:

```python
def calculate_edge_weight(current_cell, neighbor_cell):
    """
    Calcula el peso de la arista considerando tráfico y semáforos.
    """
    base_weight = 1

    # Penalizar si hay muchos coches
    car_count = sum(1 for agent in neighbor_cell.agents
                    if isinstance(agent, Car))
    traffic_penalty = car_count * 0.5

    # Penalizar si hay semáforo (asumiendo tiempo de espera)
    traffic_light_penalty = 0
    for agent in neighbor_cell.agents:
        if isinstance(agent, Traffic_Light):
            if not agent.state:  # Rojo
                traffic_light_penalty = 5
            break

    return base_weight + traffic_penalty + traffic_light_penalty
```

### Ventajas de Dijkstra vs. Implementación Actual

| Aspecto | Actual | Con Dijkstra |
|---------|--------|--------------|
| **Planificación** | No existe | Ruta completa calculada |
| **Optimalidad** | No garantizada | Camino más corto garantizado |
| **Eficiencia** | Movimiento aleatorio | Movimiento dirigido |
| **Destino** | Puede no llegar | Garantiza llegar (si existe camino) |
| **Tráfico** | No considera | Puede considerar (con pesos) |

### Diferencia entre Dijkstra y A*

El código tiene un método vacío `aStar()`. Aquí la diferencia:

**Dijkstra:**
- Explora en todas direcciones uniformemente
- No usa información del destino
- Encuentra camino más corto garantizado
- Más lento que A* pero más simple

**A\* (A-Star):**
- Usa heurística (ej: distancia Manhattan) hacia el destino
- Explora de forma dirigida hacia el objetivo
- Encuentra camino más corto garantizado (con heurística admisible)
- Más rápido que Dijkstra en la mayoría de casos

Para este proyecto, **recomiendo A*** si el grid es grande. Para grids pequeños (<50x50), Dijkstra es suficiente.

### Implementación de A* (Opcional)

```python
def heuristic(a, b):
    """Distancia Manhattan entre dos coordenadas."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(graph, start, end):
    """
    Calcula el camino más corto usando A*.
    """
    pq = [(0, start)]
    g_score = {start: 0}
    f_score = {start: heuristic(start, end)}
    previous = {start: None}
    visited = set()

    while pq:
        _, current = heapq.heappop(pq)

        if current in visited:
            continue
        visited.add(current)

        if current == end:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1]

        if current not in graph:
            continue

        for neighbor, weight in graph[current]:
            tentative_g = g_score[current] + weight

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                previous[neighbor] = current
                heapq.heappush(pq, (f_score[neighbor], neighbor))

    return None
```

## Pasos de Implementación

1. **Agregar el método `build_graph()` al modelo**
2. **Implementar `dijkstra()` o `astar()` como función del módulo**
3. **Modificar la clase `Car`:**
   - Agregar atributos `path` y `path_index`
   - Implementar `recalculate_path()`
   - Reescribir `move()` para seguir el camino
4. **Construir el grafo en la inicialización del modelo**
5. **Probar con diferentes configuraciones de tráfico**

## Consideraciones de Rendimiento

- **Frecuencia de recalculación**: No recalcular en cada step, solo cuando sea necesario
- **Caché**: Guardar el grafo en el modelo, no reconstruirlo constantemente
- **Complejidad**: Dijkstra es O((V + E) log V) donde V = nodos, E = aristas
- Para un grid de 24x24 = 576 celdas, el rendimiento es aceptable

## Ejemplo de Uso

```python
# En el modelo, después de crear todas las Roads
model.graph = build_graph(model)

# Cada coche calcula su ruta al inicializarse
car = Car(model, initial_cell)
# Automáticamente llama a recalculate_path() en __init__

# En cada step, el coche sigue su camino
car.step()  # Llama a move() que sigue el path calculado
```

## Referencias

- [Algoritmo de Dijkstra - Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [A* Pathfinding - Wikipedia](https://en.wikipedia.org/wiki/A*_search_algorithm)
- [Mesa Documentation](https://mesa.readthedocs.io/)
