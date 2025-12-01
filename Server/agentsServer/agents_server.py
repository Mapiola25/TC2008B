# TC2008B. Sistemas Multiagentes y Gráficas Computacionales
# Python flask server to interact with webGL.
# Octavio Navarro. 2024

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from randomAgents.model import CityModel
from randomAgents.agent import *

from mesa.visualization import Slider, SolaraViz, make_space_component
from mesa.visualization.components import AgentPortrayalStyle

# Size of the board:
number_agents = 10
width = 28
height = 28
randomModel = None
currentStep = 0

# This application will be used to interact with WebGL
app = Flask("Traffic example")
cors = CORS(app, origins=['http://localhost'])

# This route will be used to send the parameters of the simulation to the server.
# The servers expects a POST request with the parameters in a.json.
@app.route('/init', methods=['GET', 'POST'])
@cross_origin()
def initModel():
    global currentStep, randomModel, number_agents

    if request.method == 'POST':
        try:
            number_agents = int(request.json.get('N', 10))
            currentStep = 0
        except Exception as e:
            print(e)
            return jsonify({"message": "Error initializing the model"}), 500

    # Reset current step
    currentStep = 0

    print(f"Model parameters: N={number_agents}")

    # Create the model using the parameters sent by the application
    randomModel = CityModel(N=number_agents)

    # Return a message to saying that the model was created successfully
    return jsonify({"message": f"Parameters received, model initiated.\nNumber of agents: {number_agents}"})


# This route will be used to get the positions of the agents
@app.route('/getAgents', methods=['GET'])
@cross_origin()
def getAgents():
    global randomModel

    if request.method == 'GET':
        # Get the positions of the agents and return them to WebGL in JSON.json.t.
        # Note that the positions are sent as a list of dictionaries, where each dictionary has the id and position of an agent.
        # The y coordinate is set to 1, since the agents are in a 3D world. The z coordinate corresponds to the row (y coordinate) of the grid in mesa.
        try:
            agentCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Car) for obj in cell.agents)
            ).cells
            # print(f"CELLS: {agentCells}")

            agents = [
                (cell.coordinate, agent)
                for cell in agentCells
                for agent in cell.agents
                if isinstance(agent, Car)
            ]
            # print(f"AGENTS: {agents}")

            agentPositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":1, "z":coordinate[1]}
                for (coordinate, a) in agents
            ]
            # print(f"AGENT POSITIONS: {agentPositions}")

            return jsonify({'positions': agentPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with the agent positions"}), 500

# This route will be used to get the positions of the obstacles
@app.route('/getObstacles', methods=['GET'])
@cross_origin()
def getObstacles():
    global randomModel

    if request.method == 'GET':
        try:
            # Get the positions of the obstacles and return them to WebGL in JSON.json.t.
            # Same as before, the positions are sent as a list of dictionaries, where each dictionary has the id and position of an obstacle.

            obstacleCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Obstacle) for obj in cell.agents)
            )
            # print(f"CELLS: {agentCells}")

            agents = [
                (cell.coordinate, agent)
                for cell in obstacleCells
                for agent in cell.agents
                if isinstance(agent, Obstacle)
            ]
            # print(f"AGENTS: {agents}")

            obstaclePositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":0, "z":coordinate[1]}
                for (coordinate, a) in agents
            ]
            # print(f"OBSTACLE POSITIONS: {obstaclePositions}")

            return jsonify({'positions': obstaclePositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with obstacle positions"}), 500

@app.route('/getDestinations', methods=['GET'])
@cross_origin()
def getDestinations():
    global randomModel

    if request.method == 'GET':
        try:
            # Get the positions of the obstacles and return them to WebGL in JSON.json.t.
            # Same as before, the positions are sent as a list of dictionaries, where each dictionary has the id and position of an obstacle.

            destinationCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Destination) for obj in cell.agents)
            )
            # print(f"CELLS: {agentCells}")

            agents = [
                (cell.coordinate, agent)
                for cell in destinationCells
                for agent in cell.agents
                if isinstance(agent, Destination)
            ]
            # print(f"AGENTS: {agents}")

            destinationPositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":1, "z":coordinate[1]}
                for (coordinate, a) in agents
            ]
            # print(f"OBSTACLE POSITIONS: {obstaclePositions}")

            return jsonify({'positions': destinationPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with destination positions"}), 500

@app.route('/getRoads', methods=['GET'])
@cross_origin()
def getRoads():
    global randomModel

    if request.method == 'GET':
        try:
            # Get the positions of the obstacles and return them to WebGL in JSON.json.t.
            # Same as before, the positions are sent as a list of dictionaries, where each dictionary has the id and position of an obstacle.

            roadCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Road) for obj in cell.agents)
            )
            # print(f"CELLS: {agentCells}")

            agents = [
                (cell.coordinate, agent)
                for cell in roadCells
                for agent in cell.agents
                if isinstance(agent, Road)
            ]
            # print(f"AGENTS: {agents}")

            roadPositions = [
                {"id": str(a.unique_id), "x": coordinate[0], "y":0, "z":coordinate[1]}
                for (coordinate, a) in agents
            ]
            # print(f"OBSTACLE POSITIONS: {obstaclePositions}")

            return jsonify({'positions': roadPositions})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error with obstacle positions"}), 500
        
@app.route('/getTlights', methods=['GET'])
@cross_origin()
def getTlights():
    global randomModel

    if request.method == 'GET':
        try:
            tlCells = randomModel.grid.all_cells.select(
                lambda cell: any(isinstance(obj, Traffic_Light) for obj in cell.agents)
            )

            tls = [
                (cell.coordinate, agent)
                for cell in tlCells
                for agent in cell.agents
                if isinstance(agent, Traffic_Light)
            ]

            tlPositions = [
                {
                    "id": str(a.unique_id),
                    "x": coordinate[0],
                    "y": 1,                     
                    "z": coordinate[1],
                    "state": "green" if a.state else "red"
                }
                for (coordinate, a) in tls
            ]

            return jsonify({'positions': tlPositions})

        except Exception as e:
            print(e)
            return jsonify({"message": "Error with traffic light positions"}), 500

# This route will be used to update the model
@app.route('/update', methods=['GET'])
@cross_origin()
def updateModel():
    global currentStep, randomModel
    if request.method == 'GET':
        try:
        # Update the model and return a message to WebGL saying that the model was updated successfully
            randomModel.step()
            currentStep += 1
            return jsonify({'message': f'Model updated to step {currentStep}.', 'currentStep':currentStep})
        except Exception as e:
            print(e)
            return jsonify({"message": "Error during step."}), 500
        
@app.route('/setCarSpawnRate', methods=['POST'])
@cross_origin()
def setCarSpawnRate():
    global randomModel

    try:
        data = request.json
        new_rate = int(data.get("rate", 5))

        # Guardamos el valor en el modelo MESA
        randomModel.car_spawn_rate = new_rate

        print(f"[SERVER] spawnRate actualizado a {new_rate}")

        return jsonify({"message": f"spawnRate actualizado a {new_rate}"}), 200

    except Exception as e:
        print("ERROR en setCarSpawnRate:", e)
        return jsonify({"error": "No se pudo actualizar spawnRate"}), 500


if __name__=='__main__':
    # Run the flask server in port 8585
    app.run(host="localhost", port=8585, debug=True)
