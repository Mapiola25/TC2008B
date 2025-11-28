# Implementación del Algoritmo A* para Navegación de Coches

## Índice
1. [Introducción](#introducción)
2. [¿Por qué A*?](#por-qué-a)
3. [Conceptos Fundamentales](#conceptos-fundamentales)
4. [Arquitectura de la Implementación](#arquitectura-de-la-implementación)
5. [Implementación Paso a Paso](#implementación-paso-a-paso)
6. [Modificaciones al Código Actual](#modificaciones-al-código-actual)
7. [Consideraciones Especiales](#consideraciones-especiales)
8. [Ejemplo de Uso](#ejemplo-de-uso)

---

## Introducción

Este documento describe cómo implementar el algoritmo **A*** (A-Star) en el sistema de simulación de tráfico urbano para que los coches naveguen inteligentemente desde su posición actual hasta sus destinos asignados.

### Estado Actual del Sistema
- **Ubicación**: `Server/agentsServer/randomAgents/`
- **Archivos principales**:
  - `agent.py`: Define los agentes (Car, Road, Traffic_Light, Destination, Obstacle)
  - `model.py`: Define el modelo de la ciudad
- **Comportamiento actual**: Los coches se mueven de forma simple siguiendo la dirección de las calles sin planificación de ruta

### Objetivo
Implementar A* para que cada coche:
1. Calcule la ruta óptima desde su posición hasta su destino
2. Respete las direcciones de las calles
3. Considere los semáforos
4. Evite obstáculos
5. Minimice la distancia recorrida

---

## ¿Por qué A*?

A* es ideal para este problema porque:

| Característica | Beneficio para el Proyecto |
|---------------|---------------------------|
| **Óptimo** | Garantiza encontrar la ruta más corta si existe |
| **Eficiente** | Usa heurística para explorar menos nodos que Dijkstra |
| **Completo** | Siempre encuentra una solución si existe |
| **Adaptable** | Puede incorporar restricciones (direcciones, semáforos) |

### Comparación con Alternativas

```
Dijkstra:  Explora todos los nodos de forma uniforme (más lento)
A*:        Explora primero los nodos más prometedores (más rápido)
Greedy:    Solo usa heurística (puede no ser óptimo)
```

---

## Conceptos Fundamentales

### Fórmula de A*

```
f(n) = g(n) + h(n)
```

Donde:
- **f(n)**: Costo total estimado del nodo `n`
- **g(n)**: Costo real desde el inicio hasta `n`
- **h(n)**: Costo estimado (heurística) desde `n` hasta el destino

### Heurística Recomendada: Distancia de Manhattan

Para una cuadrícula ortogonal (como la ciudad), la distancia de Manhattan es óptima:

```python
h(n) = |n.x - destino.x| + |n.y - destino.y|
```

**¿Por qué Manhattan y no Euclidiana?**
- Los coches solo pueden moverse en 4 direcciones (arriba, abajo, izquierda, derecha)
- Manhattan refleja mejor la distancia real que debe recorrer el coche
- Es admisible (nunca sobreestima) y consistente

---

## Arquitectura de la Implementación

### Estructura de Datos Necesarias

```python
# Nodo en la búsqueda A*
class AStarNode:
    def __init__(self, cell, parent=None):
        self.cell = cell           # Celda del grid
        self.parent = parent       # Nodo padre (para reconstruir ruta)
        self.g = 0                 # Costo desde inicio
        self.h = 0                 # Heurística al destino
        self.f = 0                 # Costo total (g + h)
```

### Componentes Principales

1. **Cola de Prioridad (Open Set)**
   - Almacena nodos por explorar
   - Ordenados por costo `f(n)` menor primero
   - Implementación: `heapq` o `PriorityQueue`

2. **Conjunto Cerrado (Closed Set)**
   - Almacena nodos ya explorados
   - Evita procesarlos múltiples veces
   - Implementación: `set` con coordenadas

3. **Función Heurística**
   - Calcula distancia estimada al destino
   - Debe ser admisible y consistente

4. **Reconstrucción de Ruta**
   - Sigue punteros `parent` desde destino hasta inicio
   - Retorna lista de celdas en orden

---

## Implementación Paso a Paso

### Paso 1: Importar Librerías Necesarias

```python
import heapq
from typing import List, Tuple, Optional
```

### Paso 2: Implementar la Función Heurística

```python
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
```

### Paso 3: Verificar si una Celda es Transitable

```python
def is_walkable(self, cell, direction_from_parent=None):
    """
    Verifica si un coche puede moverse a una celda específica.

    Args:
        cell: Celda a verificar
        direction_from_parent: Dirección desde la celda padre

    Returns:
        bool: True si la celda es transitable
    """
    # Buscar agentes en la celda
    road_agent = None
    traffic_light = None
    has_obstacle = False

    for agent in cell.agents:
        if isinstance(agent, Road):
            road_agent = agent
        elif isinstance(agent, Traffic_Light):
            traffic_light = agent
        elif isinstance(agent, Obstacle):
            has_obstacle = True
        elif isinstance(agent, Destination):
            # Los destinos siempre son transitables
            return True

    # No se puede pasar por obstáculos
    if has_obstacle:
        return False

    # Debe haber una calle
    if not road_agent:
        return False

    # Verificar dirección si se especifica
    if direction_from_parent:
        if road_agent.direction != direction_from_parent:
            return False

    return True
```

### Paso 4: Calcular Dirección del Movimiento

```python
def get_direction(self, from_cell, to_cell):
    """
    Calcula la dirección del movimiento entre dos celdas.

    Args:
        from_cell: Celda de origen
        to_cell: Celda de destino

    Returns:
        str: Dirección ("Up", "Down", "Left", "Right") o None
    """
    dx = to_cell.coordinate[0] - from_cell.coordinate[0]
    dy = to_cell.coordinate[1] - from_cell.coordinate[1]

    if dx > 0 and dy == 0:
        return "Right"
    elif dx < 0 and dy == 0:
        return "Left"
    elif dy > 0 and dx == 0:
        return "Up"
    elif dy < 0 and dx == 0:
        return "Down"

    return None
```

### Paso 5: Implementar el Algoritmo A* Completo

```python
def aStar(self):
    """
    Implementa el algoritmo A* para encontrar la ruta óptima al destino.

    Returns:
        List[Cell]: Lista de celdas que forman la ruta óptima, o None si no hay ruta
    """
    start = self.cell
    goal = self.destination

    # Verificar si ya estamos en el destino
    if start == goal:
        return [start]

    # Inicializar estructuras de datos
    open_set = []
    closed_set = set()

    # Diccionarios para almacenar g, h, f y parents
    g_score = {start.coordinate: 0}
    f_score = {start.coordinate: heuristic(start, goal)}
    parent_map = {}

    # Agregar nodo inicial a open_set
    heapq.heappush(open_set, (f_score[start.coordinate], start.coordinate, start))

    while open_set:
        # Obtener el nodo con menor f_score
        current_f, current_coord, current_cell = heapq.heappop(open_set)

        # Si llegamos al destino, reconstruir ruta
        if current_cell == goal:
            return self.reconstruct_path(parent_map, current_cell)

        # Marcar como explorado
        closed_set.add(current_coord)

        # Explorar vecinos
        for neighbor in current_cell.neighborhood:
            neighbor_coord = neighbor.coordinate

            # Saltar si ya fue explorado
            if neighbor_coord in closed_set:
                continue

            # Calcular dirección del movimiento
            direction = self.get_direction(current_cell, neighbor)

            # Verificar si es transitable con la dirección correcta
            if not self.is_walkable(neighbor, direction):
                continue

            # Calcular nuevo g_score
            tentative_g = g_score[current_coord] + 1  # Costo de 1 por movimiento

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
    print(f"No se encontró ruta desde {start.coordinate} hasta {goal.coordinate}")
    return None
```

### Paso 6: Reconstruir la Ruta

```python
def reconstruct_path(self, parent_map, current_cell):
    """
    Reconstruye la ruta desde el inicio hasta el destino.

    Args:
        parent_map: Diccionario de padres
        current_cell: Celda final (destino)

    Returns:
        List[Cell]: Ruta completa desde inicio hasta destino
    """
    path = [current_cell]
    current_coord = current_cell.coordinate

    while current_coord in parent_map:
        current_cell = parent_map[current_coord]
        path.append(current_cell)
        current_coord = current_cell.coordinate

    path.reverse()  # Invertir para tener la ruta desde inicio a fin
    return path
```

---

## Modificaciones al Código Actual

### Cambios en `agent.py`

#### 1. Modificar el Constructor de `Car`

```python
class Car(CellAgent):
    def __init__(self, model, cell):
        super().__init__(model)
        self.destination = random.choice(destinations)
        self.cell = cell
        self.path = None  # Ruta calculada por A*
        self.path_index = 0  # Índice actual en la ruta
```

#### 2. Reemplazar el Método `aStar()` (línea 22-23)

Reemplazar:
```python
def aStar():
    pass
```

Con la implementación completa del Paso 5.

#### 3. Modificar el Método `move()` (línea 25-93)

```python
def move(self):
    """
    Mueve el coche siguiendo la ruta calculada por A*.
    """
    # Si no hay ruta calculada, calcularla
    if self.path is None:
        self.path = self.aStar()
        if self.path is None:
            print(f"Coche en {self.cell.coordinate}: No se puede llegar al destino {self.destination.coordinate}")
            return
        self.path_index = 0

    # Si ya llegamos al destino
    if self.path_index >= len(self.path) - 1:
        print(f"Coche llegó al destino {self.destination.coordinate}")
        # Aquí puedes eliminar el coche o asignarle un nuevo destino
        return

    # Siguiente celda en la ruta
    next_cell = self.path[self.path_index + 1]

    # Verificar si hay semáforo en la siguiente celda
    traffic_light = None
    for agent in next_cell.agents:
        if isinstance(agent, Traffic_Light):
            traffic_light = agent
            break

    # Si hay semáforo y está en rojo, esperar
    if traffic_light and not traffic_light.state:
        print(f"Coche en {self.cell.coordinate}: Esperando semáforo en rojo")
        return

    # Verificar si hay otro coche en la siguiente celda
    has_car = any(isinstance(agent, Car) for agent in next_cell.agents)
    if has_car:
        print(f"Coche en {self.cell.coordinate}: Esperando a otro coche")
        return

    # Moverse a la siguiente celda
    self.move_to(next_cell)
    self.path_index += 1
    print(f"Coche movido a {self.cell.coordinate}")
```

#### 4. Agregar Métodos Auxiliares

Agregar después del método `move()`:

```python
# Agregar los métodos implementados en los Pasos 2-6
# - heuristic()
# - is_walkable()
# - get_direction()
# - reconstruct_path()
```

---

## Consideraciones Especiales

### 1. Recalcular Ruta Dinámicamente

Si los semáforos o el tráfico cambian, puede ser necesario recalcular:

```python
def should_recalculate_path(self):
    """
    Determina si se debe recalcular la ruta.
    """
    # Recalcular cada N pasos
    if self.model.current_step % 50 == 0:
        return True

    # Recalcular si estamos bloqueados por mucho tiempo
    if hasattr(self, 'stuck_counter') and self.stuck_counter > 10:
        return True

    return False

def move(self):
    # ... código anterior ...

    if self.should_recalculate_path():
        print(f"Recalculando ruta para coche en {self.cell.coordinate}")
        self.path = None
        self.stuck_counter = 0
```

### 2. Costo Variable por Semáforos

Puedes ajustar el costo de pasar por semáforos:

```python
# En el método aStar(), al calcular tentative_g:
tentative_g = g_score[current_coord] + self.get_move_cost(current_cell, neighbor)

def get_move_cost(self, from_cell, to_cell):
    """
    Calcula el costo de moverse entre dos celdas.
    """
    base_cost = 1

    # Aumentar costo si hay semáforo
    for agent in to_cell.agents:
        if isinstance(agent, Traffic_Light):
            base_cost += 2  # Penalización por semáforo

    return base_cost
```

### 3. Evitar Colisiones

```python
def is_walkable(self, cell, direction_from_parent=None):
    # ... código anterior ...

    # Evitar celdas con otros coches (excepto el destino)
    has_car = any(isinstance(agent, Car) for agent in cell.agents)
    if has_car and cell != self.destination:
        return False

    return True
```

### 4. Optimización de Rendimiento

Para mapas grandes:

```python
# Cache de rutas calculadas (a nivel de modelo)
if not hasattr(self.model, 'path_cache'):
    self.model.path_cache = {}

def aStar(self):
    cache_key = (self.cell.coordinate, self.destination.coordinate)

    if cache_key in self.model.path_cache:
        return self.model.path_cache[cache_key].copy()

    path = # ... calcular con A* ...

    if path:
        self.model.path_cache[cache_key] = path.copy()

    return path
```

---

## Ejemplo de Uso

### Antes (movimiento simple):

```python
# agent.py - línea 25-93
def move(self):
    neighbors = list(self.cell.neighborhood)
    next_move = None
    # ... lógica simple que solo mira vecinos inmediatos ...
```

**Problema**: El coche no planifica, puede dar vueltas o tomar rutas subóptimas.

### Después (con A*):

```python
# agent.py
def move(self):
    if self.path is None:
        self.path = self.aStar()  # Calcula ruta óptima completa

    next_cell = self.path[self.path_index + 1]
    # ... verificar semáforos y moverse ...
```

**Beneficio**: El coche conoce toda la ruta de antemano y toma el camino más corto.

### Visualización del Comportamiento

```
Situación: Coche en (0,0) quiere ir a (23,24)

Sin A*:
(0,0) → (1,0) → (1,1) → (2,1) → (1,2) ← se da vuelta! → ...
Pasos: ~60-80 (aleatorio)

Con A*:
(0,0) → (1,0) → (2,0) → ... → (23,24)
Pasos: ~47 (óptimo)
```

---

## Resumen de Archivos a Modificar

| Archivo | Líneas | Modificación |
|---------|--------|-------------|
| `agent.py` | 11-20 | Agregar atributos `path` y `path_index` al constructor de `Car` |
| `agent.py` | 22-23 | Implementar método `aStar()` completo |
| `agent.py` | 25-93 | Reemplazar método `move()` para usar A* |
| `agent.py` | Nueva | Agregar métodos auxiliares: `heuristic()`, `is_walkable()`, `get_direction()`, `reconstruct_path()` |

---

## Próximos Pasos

1. **Implementar A* básico**: Seguir los pasos 1-6
2. **Probar con un solo coche**: Verificar que llegue al destino
3. **Agregar manejo de semáforos**: Implementar espera en rojo
4. **Manejar colisiones**: Evitar que dos coches ocupen la misma celda
5. **Optimizar**: Agregar cache, recalculación dinámica
6. **Visualizar**: Agregar logs o visualización de rutas

---

## Referencias

- [A* Pathfinding Tutorial](https://www.redblobgames.com/pathfinding/a-star/introduction.html)
- [Python heapq Documentation](https://docs.python.org/3/library/heapq.html)
- Mesa Framework: [https://mesa.readthedocs.io/](https://mesa.readthedocs.io/)

---

**Creado para**: TC2008B - Simulación de Tráfico Urbano
**Versión**: 1.0
**Última actualización**: 2025-11-27
