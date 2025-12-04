/*
 * Functions to connect to an external API to get the coordinates of agents
 *
 * Gilberto Echeverria
 * 2025-11-08
 */


'use strict';

import { Object3D } from '../libs/object3d';

// Define the agent server URI
const agent_server_uri = "http://localhost:8585/";

// Initialize arrays to store agents and obstacles
const agents = [];
const obstacles = [];
const roads = [];
const tlights= [];
const destinations = [];
let currentStep = 0;
let carsSpawned = 0;
let carsArrived = 0;

// Define the data object
const initData = {
    NAgents: 20,
    width: 28,
    height: 28
};


/* FUNCTIONS FOR THE INTERACTION WITH THE MESA SERVER */

/*
 * Initializes the agents model by sending a POST request to the agent server.
 */
async function initAgentsModel() {
    try {
        // Send a POST request to the agent server to initialize the model
        let response = await fetch(agent_server_uri + "init", {
            method: 'POST',
            headers: { 'Content-Type':'application/json' },
            body: JSON.stringify(initData)
        });

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON and log the message
            let result = await response.json();
            console.log(result.message);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

/*
 * Retrieves the current positions of all agents from the agent server.
 */
async function getAgents() {
    try {
        let response = await fetch(agent_server_uri + "getAgents");

        if (response.ok) {
            let result = await response.json();

            const serverAgentIds = new Set(result.positions.map(agent => agent.id));

            // Update existing agents and add new ones
            for (const agent of result.positions) {
                const current_agent = agents.find((object3d) => object3d.id == agent.id);

                if(current_agent != undefined){
                    current_agent.oldPosArray = current_agent.posArray;
                    current_agent.position = {x: agent.x, y: agent.y, z: agent.z};
                    current_agent.type = agent.type || "Car";  // Actualizar tipo
                    current_agent.crashed = agent.crashed || false;  // Estado de choque
                    current_agent.crash_timer = agent.crash_timer || 0;  // Temporizador de choque
                } else {
                    const newAgent = new Object3D(agent.id, [agent.x, agent.y, agent.z]);
                    newAgent['oldPosArray'] = newAgent.posArray;
                    newAgent.type = agent.type || "Car";  // Guardar tipo de agente
                    newAgent.crashed = agent.crashed || false;  // Estado de choque
                    newAgent.crash_timer = agent.crash_timer || 0;  // Temporizador de choque
                    agents.push(newAgent);
                }
            }

            // Eliminar agentes que ya no están en el servidor (llegaron a su destino)
            for (let i = agents.length - 1; i >= 0; i--) {
                if (!serverAgentIds.has(agents[i].id)) {
                    agents.splice(i, 1);
                }
            }
        }

    } catch (error) {
        console.log(error);
    }
}

/*
 * Retrieves the current positions of all obstacles from the agent server.
 */
async function getObstacles() {
    try {
        // Send a GET request to the agent server to retrieve the obstacle positions
        let response = await fetch(agent_server_uri + "getObstacles");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Create new obstacles and add them to the obstacles array
            for (const obstacle of result.positions) {
                const newObstacle = new Object3D(obstacle.id, [obstacle.x, obstacle.y, obstacle.z]);
                obstacles.push(newObstacle);
            }
            // Log the obstacles array
            //console.log("Obstacles:", obstacles);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

async function getDestinations() {
    try {
        // Send a GET request to the agent server to retrieve the obstacle positions
        let response = await fetch(agent_server_uri + "getDestinations");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Create new destination and add them to the destination array
            for (const destination of result.positions) {
                const newDestination = new Object3D(destination.id, [destination.x, destination.y, destination.z]);
                destinations.push(newDestination);
            }
            // Log the destination array
            //console.log("destination:", destination);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

async function getRoads() {
    try {
        // Send a GET request to the agent server to retrieve the obstacle positions
        let response = await fetch(agent_server_uri + "getRoads");

        // Check if the response was successful
        if (response.ok) {
            // Parse the response as JSON
            let result = await response.json();

            // Create new obstacles and add them to the obstacles array
            for (const road of result.positions) {
                const newRoad = new Object3D(road.id, [road.x, road.y, road.z]);
                newRoad.direction = road.direction || "Left";
                roads.push(newRoad);
            }
            // Log the obstacles array
            //console.log("Obstacles:", obstacles);
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

async function getTlights() {
    try {
        let response = await fetch(agent_server_uri + "getTlights");

        if (response.ok) {
            let result = await response.json();

            // First time: create the lights
            if (tlights.length === 0) {
                for (const tl of result.positions) {
                    const newLight = new Object3D(tl.id, [tl.x, tl.y, tl.z]);
                    newLight.state = tl.state;
                    tlights.push(newLight);
                }
            } 
            else {
                // Update existing lights
                for (const tl of result.positions) {
                    const existing = tlights.find(obj => obj.id == tl.id);

                    if (existing) {
                        existing.position = { x: tl.x, y: tl.y, z: tl.z };
                        existing.state = tl.state;
                    }
                }
            }
        }
    } catch (error) {
        console.log(error);
    }
}

/*
 * Updates the agent positions by sending a request to the agent server.
 */
async function update() {
    try {
        // Send a request to the agent server to update the agent positions
        let response = await fetch(agent_server_uri + "update");

        // Check if the response was successful
        if (response.ok) {
            let result = await response.json();
            currentStep = result.currentStep || 0;
            carsSpawned = result.carsSpawned || 0;
            carsArrived = result.carsArrived || 0;

            // Retrieve the updated agent positions
            await getAgents();
            await getTlights();
            for (const tl of tlights){
                if (tl.state === "red")
                    tl.color = [1,0,0,1];
                else if (tl.state === "yellow")
                    tl.color = [1,1,0,1];
                else if (tl.state === "green")
                    tl.color = [0,1,0,1];
            }
            // Log a message indicating that the agents have been updated
            //console.log("Updated agents");
        }

    } catch (error) {
        // Log any errors that occur during the request
        console.log(error);
    }
}

export { agents, obstacles, roads, destinations, initAgentsModel, update, getAgents, getObstacles, getRoads, tlights, getTlights, getDestinations, currentStep, carsSpawned, carsArrived };
