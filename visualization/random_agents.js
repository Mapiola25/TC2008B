/*
 * Base program for a 3D scene that connects to an API to get the movement
 * of agents.
 * The scene shows textured buildings, cars, roads and traffic lights.
 *
 * Gilberto Echeverria
 * 2025-11-08
 */

"use strict";

import * as twgl from "twgl-base.js";
import GUI from "lil-gui";
import { M4 } from "../libs/3d-lib";
import { Scene3D } from "../libs/scene3d";
import { Object3D } from "../libs/object3d";
import { Camera3D } from "../libs/camera3d";
import { cubeSkybox } from "../libs/shapes";

// --------- BUILDINGS ----------
import buildingAClean from "../newAssets/buildings/building-a-clean.obj?raw";
import buildingBClean from "../newAssets/buildings/building-b-clean.obj?raw";
import buildingCClean from "../newAssets/buildings/building-c-clean.obj?raw";
import buildingDClean from "../newAssets/buildings/building-d-clean.obj?raw";
import buildingEClean from "../newAssets/buildings/building-e-clean.obj?raw";
import buildingGClean from "../newAssets/buildings/building-g-clean.obj?raw";
import buildingHClean from "../newAssets/buildings/building-h-clean.obj?raw";
import buildingIClean from "../newAssets/buildings/building-i-clean.obj?raw";
import buildingJClean from "../newAssets/buildings/building-j-clean.obj?raw";
import buildingKClean from "../newAssets/buildings/building-k-clean.obj?raw";
import buildingLClean from "../newAssets/buildings/building-l-clean.obj?raw";
import buildingMClean from "../newAssets/buildings/building-m-clean.obj?raw";
import buildingNClean from "../newAssets/buildings/building-n-clean.obj?raw";
import buildingSkyscraperAClean from "../newAssets/buildings/building-skyscraper-a-clean.obj?raw";
import buildingSkyscraperBClean from "../newAssets/buildings/building-skyscraper-b-clean.obj?raw";
import buildingSkyscraperCClean from "../newAssets/buildings/building-skyscraper-c-clean.obj?raw";
import buildingSkyscraperDClean from "../newAssets/buildings/building-skyscraper-d-clean.obj?raw";
import buildingSkyscraperEClean from "../newAssets/buildings/building-skyscraper-e-clean.obj?raw";

// --------- CARS ----------
import sedanBody from "../newAssets/models/vehicles/sedan_sin_llantas.obj?raw";
import sedanSportBody from "../newAssets/models/vehicles/sedan_sport_sin_llantas.obj?raw";
import raceBody from "../newAssets/models/vehicles/race_sin_llantas.obj?raw";
import hatchbackSportBody from "../newAssets/models/vehicles/hatchback_sport_sin_llantas.obj?raw";

// --------- WHEELS ----------
import sedanWheel from "../newAssets/models/vehicles/llanta_sedan.obj?raw";
import sedanSportWheel from "../newAssets/models/vehicles/llanta_sedan_sport.obj?raw";
import raceWheel from "../newAssets/models/vehicles/llanta_race.obj?raw";
import hatchbackSportWheel from "../newAssets/models/vehicles/llanta_hatchback_sport.obj?raw";

// --------- TRAFFIC LIGHT ----------
import trafficLightModel from "../newAssets/signs/model.obj?raw";

// --------- ROADS ----------
import roadStraight from "../newAssets/roads/road-straight.obj?raw";
import roadBend from "../newAssets/roads/road-bend.obj?raw";
import roadIntersection from "../newAssets/roads/road-intersection.obj?raw";
import roadIntersectionPath from "../newAssets/roads/road-intersection-path.obj?raw";

// --------- TEXTURES ----------
import colormap from "../newAssets/buildings/Textures/colormap.png";
import vehiclesColormap from "../newAssets/models/vehicles/Textures/colormap.png";
import roadsColormap from "../newAssets/roads/Textures/colormap.png";
import skyboxTexture from "../assets/textures/Skyboxes/image-night.png";

// --------- API MODEL ----------
import {
  agents,
  obstacles,
  initAgentsModel,
  update,
  getAgents,
  getObstacles,
  getRoads,
  getDestinations,
  destinations,
  roads,
  tlights,
  getTlights,
  currentStep,
  carsSpawned,
  carsArrived,
} from "../libs/api_connection.js";

// --------- SHADERS ----------
import vsGLSL from "../assets/shaders/vs_color.glsl?raw";
import fsGLSL from "../assets/shaders/fs_color.glsl?raw";
import vsTextureGLSL from "../assets/shaders/vs_multi_lights_attenuation.glsl?raw";
import fsTextureGLSL from "../assets/shaders/fs_multi_lights_attenuation.glsl?raw";
import vsSkyboxGLSL from "../assets/shaders/vs_flat_textures.glsl?raw";
import fsSkyboxGLSL from "../assets/shaders/fs_flat_textures.glsl?raw";

const scene = new Scene3D();

// Global variables
let colorProgramInfo = undefined;
let textureProgramInfo = undefined;
let skyboxProgramInfo = undefined;

let buildingTexture = undefined;
const buildingTemplates = [];

let carTexture = undefined;
const carBodyTemplates = [];
const carWheelTemplates = [];

const CAR_TYPE_OFFSETS = [
  // Sedan
  [
    [0.48, 0.3, 0.7], // delantera derecha
    [-0.48, 0.3, 0.7], // delantera izquierda
    [0.48, 0.3, -0.7], // trasera derecha
    [-0.48, 0.3, -0.7], // trasera izquierda
  ],
  // Sedan Sport 
  [
    [0.46, 0.3, 0.7],
    [-0.46, 0.3, 0.7],
    [0.46, 0.3, -0.7],
    [-0.46, 0.3, -0.7],
  ],
  // Race 
  [
    [0.44, 0.28, 0.75],
    [-0.44, 0.28, 0.75],
    [0.44, 0.28, -0.75],
    [-0.44, 0.28, -0.75],
  ],
  // Hatchback Sport 
  [
    [0.46, 0.3, 0.72],
    [-0.46, 0.3, 0.72],
    [0.46, 0.3, -0.72],
    [-0.46, 0.3, -0.72],
  ],
];

let stoplightTemplate = undefined;

let roadTexture = undefined;
let roadStraightTemplate = undefined;
let roadBendTemplate = undefined;
let roadIntersectionTemplate = undefined;
let roadIntersectionPathTemplate = undefined;

let skybox = undefined;
let skyboxTexture2D = undefined;

let gl = undefined;
const duration = 1000;
let elapsed = 0;
let then = 0;
let baseCube = undefined;
let checkpointTemplate = undefined;
let globalLightIntensity = 0.5;
let isPaused = false;
let simulationStarted = false;

// ------------------- MAIN -------------------
async function main() {
  const canvas = document.querySelector("canvas");
  gl = canvas.getContext("webgl2");
  twgl.resizeCanvasToDisplaySize(gl.canvas);
  gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

  colorProgramInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);
  textureProgramInfo = twgl.createProgramInfo(gl, [
    vsTextureGLSL,
    fsTextureGLSL,
  ]);
  skyboxProgramInfo = twgl.createProgramInfo(gl, [
    vsSkyboxGLSL,
    fsSkyboxGLSL,
  ]);

  buildingTexture = twgl.createTexture(gl, {
    min: gl.NEAREST,
    mag: gl.NEAREST,
    src: colormap,
    flipY: true,
  });

  carTexture = twgl.createTexture(gl, {
    min: gl.NEAREST,
    mag: gl.NEAREST,
    src: vehiclesColormap,
    flipY: true,
  });

  // Crear textura sólida gris uniforme para carreteras (sin marcas de carriles)
  const solidRoadColor = new Uint8Array([100, 100, 100, 255]); // Gris oscuro uniforme
  roadTexture = twgl.createTexture(gl, {
    min: gl.NEAREST,
    mag: gl.NEAREST,
    width: 1,
    height: 1,
    src: solidRoadColor,
    format: gl.RGBA,
    type: gl.UNSIGNED_BYTE,
    flipY: false,
  });

  skyboxTexture2D = twgl.createTexture(gl, {
    min: gl.LINEAR,
    mag: gl.LINEAR,
    src: skyboxTexture,
    flipY: false,
  });

  // Create skybox object
  skybox = new Object3D(-1);
  skybox.arrays = cubeSkybox(100); // Large cube
  skybox.bufferInfo = twgl.createBufferInfoFromArrays(gl, skybox.arrays);
  skybox.vao = twgl.createVAOFromBufferInfo(gl, skyboxProgramInfo, skybox.bufferInfo);
  skybox.programInfo = skyboxProgramInfo;
  skybox.texture = skyboxTexture2D;
  skybox.position = { x: 0, y: 0, z: 0 };
  skybox.scale = { x: 1, y: 1, z: 1 };
  if (!skybox.rotRad) {
    skybox.rotRad = { x: 0, y: 0, z: 0 };
  }

  await initAgentsModel();

  await getAgents();
  await getObstacles();
  await getRoads();
  await getTlights();
  await getDestinations();

  setupScene();
  setupObjects(scene, gl, colorProgramInfo);
  setupUI();

  // Iniciar el loop de renderizado (sin actualizar la simulación hasta que se presione el botón)
  drawScene();
}

// ------------------- SCENE SETUP -------------------
function setupScene() {
  let camera = new Camera3D(0, 10, 4, 0.8, [0, 0, 10], [0, 0, 0]);

  camera.panOffset = [0, 8, 0];
  scene.setCamera(camera);
  scene.camera.setupControls();

  scene.addLight(new Object3D(0, [100, 100, 100], [1, 1, 1]));
}

// ------------------- CAR SETUP -------------------
function setupCarAgent(agent) {
  // Si es Borrachito, usar solo raceBody (índice 2)
  // Si es Car normal, elegir aleatoriamente entre sedan, sedanSport y hatchbackSport (índices 0, 1, 3)
  let index;
  if (agent.type === "Borrachito") {
    index = 2; // raceBody está en el índice 2 de carBodyTemplates
  } else {
    // Excluir raceBody (índice 2) para coches normales
    const normalCarIndices = [0, 1, 3]; // sedan, sedanSport, hatchbackSport
    index = normalCarIndices[Math.floor(Math.random() * normalCarIndices.length)];
  }

  const bodyTemplate = carBodyTemplates[index];

  agent.arrays = bodyTemplate.arrays;
  agent.bufferInfo = bodyTemplate.bufferInfo;
  agent.vao = bodyTemplate.vao;
  agent.programInfo = textureProgramInfo;
  agent.texture = carTexture;
  agent.scale = { x: 0.35, y: 0.35, z: 0.35 };
  agent.color = [1, 1, 1, 1];
  agent.isCar = true;

  agent.carTypeIndex = index;

  if (!agent.rotRad) {
    agent.rotRad = { x: 0, y: 0, z: 0 };
  }
  if (!agent.prevPos) {
    agent.prevPos = [...agent.posArray];
  }

  if (!agent.wheels) {
    agent.wheels = [];
    const wheelTemplate = carWheelTemplates[index];
    const offsets = CAR_TYPE_OFFSETS[index];

    for (let i = 0; i < 4; i++) {
      const wheel = new Object3D(-1);
      wheel.arrays = wheelTemplate.arrays;
      wheel.bufferInfo = wheelTemplate.bufferInfo;
      wheel.vao = wheelTemplate.vao;

      wheel.programInfo = textureProgramInfo;
      wheel.texture = carTexture;
      wheel.color = [1, 1, 1, 1];

      wheel.scale = { x: 0.35, y: 0.35, z: 0.35 };
      wheel.rotRad = { x: 0, y: 0, z: 0 };

      wheel.localOffset = [...offsets[i]];
      wheel.parentAgent = agent;
      wheel.center = wheelTemplate.center;

      // Establecer baseRotY por llanta individual basado en el tipo de coche y posición
      // Para sedan (index 0): llantas derechas (i=0,2) usan 0, izquierdas (i=1,3) usan Math.PI
      // Para otros coches: llantas derechas usan Math.PI, izquierdas usan 0
      const isRightWheel = (i === 0 || i === 2); // índices 0 y 2 son derechas
      if (index === 0) {
        // Sedan
        wheel.baseRotY = isRightWheel ? 0.0 : Math.PI;
      } else {
        // Sedan Sport, Race, Hatchback Sport
        wheel.baseRotY = isRightWheel ? Math.PI : 0.0;
      }

      // Inicializar rotación actual de la llanta
      wheel.currentRotY = wheel.baseRotY;

      agent.wheels.push(wheel);
    }
  }

  if (!agent.wheelRotX) {
    agent.wheelRotX = [0, 0, 0, 0];
  }

  scene.addObject(agent);
}

// ------------------- OBJECTS SETUP -------------------
function setupObjects(scene, gl, programInfo) {
  baseCube = new Object3D(-1);
  baseCube.prepareVAO(gl, programInfo);

  checkpointTemplate = new Object3D(-1);
  const checkpointArrays = {
    a_position: {
      numComponents: 3,
      data: [
        // Tip (touching the ground)
        0.0, 0.0, 0.0,
        // Base triangle (hovering above)
        -0.35, 0.6, -0.28, 0.35, 0.6, -0.28, 0.0, 0.6, 0.42,
      ],
    },
    indices: {
      numComponents: 3,
      data: [0, 1, 2, 0, 2, 3, 0, 3, 1, 1, 3, 2],
    },
  };

  checkpointTemplate.arrays = checkpointArrays;
  checkpointTemplate.bufferInfo = twgl.createBufferInfoFromArrays(
    gl,
    checkpointArrays
  );
  checkpointTemplate.vao = twgl.createVAOFromBufferInfo(
    gl,
    colorProgramInfo,
    checkpointTemplate.bufferInfo
  );
  checkpointTemplate.programInfo = colorProgramInfo;

  // --- Plantillas de edificios ---
  const buildingSources = [
    buildingAClean,
    buildingBClean,
    buildingCClean,
    buildingDClean,
    buildingEClean,
    buildingGClean,
    buildingHClean,
    buildingIClean,
    buildingJClean,
    buildingKClean,
    buildingLClean,
    buildingMClean,
    buildingNClean,
    buildingSkyscraperAClean,
    buildingSkyscraperBClean,
    buildingSkyscraperCClean,
    buildingSkyscraperDClean,
    buildingSkyscraperEClean,
  ];

  for (const source of buildingSources) {
    const template = new Object3D(-1);
    template.prepareVAO(gl, textureProgramInfo, source);
    template.texture = buildingTexture;
    buildingTemplates.push(template);
  }

  // --- Plantillas de cuerpos de coche ---
  const carBodySources = [
    sedanBody,
    sedanSportBody,
    raceBody,
    hatchbackSportBody,
  ];

  for (let i = 0; i < carBodySources.length; i++) {
    const bodyTemplate = new Object3D(-1);
    bodyTemplate.prepareVAO(gl, textureProgramInfo, carBodySources[i]);
    bodyTemplate.texture = carTexture;
    carBodyTemplates.push(bodyTemplate);
  }

  // --- Plantillas de llantas ---
  const carWheelSources = [
    sedanWheel,
    sedanSportWheel,
    raceWheel,
    hatchbackSportWheel,
  ];

  for (let i = 0; i < carWheelSources.length; i++) {
    const wheelTemplate = new Object3D(-1);

    const arrays = parseAndCenterObj(carWheelSources[i]);
    wheelTemplate.arrays = arrays;
    wheelTemplate.bufferInfo = twgl.createBufferInfoFromArrays(gl, arrays);
    wheelTemplate.vao = twgl.createVAOFromBufferInfo(
      gl,
      textureProgramInfo,
      wheelTemplate.bufferInfo
    );
    wheelTemplate.programInfo = textureProgramInfo;
    wheelTemplate.texture = carTexture;

    wheelTemplate.center = [0, 0, 0];

    // No establecer baseRotY aquí, se hará por llanta individual

    carWheelTemplates.push(wheelTemplate);
  }

  // --- Plantilla de semáforo ---
  stoplightTemplate = new Object3D(-1);
  stoplightTemplate.prepareVAO(gl, colorProgramInfo, trafficLightModel);

  // --- Plantillas de carreteras ---
  roadStraightTemplate = new Object3D(-1);
  roadStraightTemplate.prepareVAO(gl, textureProgramInfo, roadStraight);
  roadStraightTemplate.texture = roadTexture;

  roadBendTemplate = new Object3D(-1);
  roadBendTemplate.prepareVAO(gl, textureProgramInfo, roadBend);
  roadBendTemplate.texture = roadTexture;

  roadIntersectionTemplate = new Object3D(-1);
  roadIntersectionTemplate.prepareVAO(gl, textureProgramInfo, roadIntersection);
  roadIntersectionTemplate.texture = roadTexture;

  roadIntersectionPathTemplate = new Object3D(-1);
  roadIntersectionPathTemplate.prepareVAO(gl, textureProgramInfo, roadIntersectionPath);
  roadIntersectionPathTemplate.texture = roadTexture;

  // ---------- Obstáculos: edificios ----------
  for (const agent of obstacles) {
    const template =
      buildingTemplates[Math.floor(Math.random() * buildingTemplates.length)];
    agent.arrays = template.arrays;
    agent.bufferInfo = template.bufferInfo;
    agent.vao = template.vao;
    agent.programInfo = textureProgramInfo;
    agent.texture = buildingTexture;
    agent.scale = { x: 0.5, y: 1.5, z: 0.5 };
    agent.color = [1, 1, 1, 1.0];
    scene.addObject(agent);

    // Piso debajo del edificio
    const pos = agent.posArray;
    const buildingFloor = new Object3D(-1, [pos[0], -0.01, pos[2]]);
    buildingFloor.arrays = baseCube.arrays;
    buildingFloor.bufferInfo = baseCube.bufferInfo;
    buildingFloor.vao = baseCube.vao;
    buildingFloor.programInfo = colorProgramInfo;
    buildingFloor.scale = { x: 1.0, y: 0.01, z: 1.0 };
    buildingFloor.color = [0.15, 0.15, 0.15, 1.0];
    scene.addObject(buildingFloor);
  }

  // ---------- Calles: usar el mismo formato (road-straight) para todas ----------
  // Todas las calles tienen la misma orientación, sin distinguir sentidos
  for (const road of roads) {
    if (!road.rotRad) {
      road.rotRad = { x: 0, y: 0, z: 0 };
    }

    // Usar road-straight para todas las carreteras (cuadradas, sin curvas)
    road.arrays = roadStraightTemplate.arrays;
    road.bufferInfo = roadStraightTemplate.bufferInfo;
    road.vao = roadStraightTemplate.vao;
    road.programInfo = textureProgramInfo;
    road.texture = roadTexture;
    road.scale = { x: 1.0, y: 1.0, z: 1.0 };
    road.color = [1, 1, 1, 1];
    
    // Sin rotación - todas las calles se ven iguales, sin distinguir sentidos
    road.rotRad.y = 0;

    scene.addObject(road);
  }

  // ---------- Destinos ----------
  for (const agent of destinations) {
    agent.arrays = checkpointTemplate.arrays;
    agent.bufferInfo = checkpointTemplate.bufferInfo;
    agent.vao = checkpointTemplate.vao;
    agent.programInfo = colorProgramInfo;
    agent.isCheckpoint = true;
    agent.color = [0.15, 0.55, 1.0, 0.8];
    agent.scale = { x: 0.9, y: 0.9, z: 0.9 };
    agent.groundY = agent.position.y;
    agent.pulseOffset = Math.random() * Math.PI * 2;
    agent.position.y = agent.groundY;
    scene.addObject(agent);
  }

  // ---------- Semáforos ----------
  for (const tl of tlights) {
    const pos = tl.posArray;
    const lateralOffset = 0.35;

    const polePos = [pos[0] + lateralOffset, pos[1], pos[2]];
    const pole = new Object3D(-1, polePos);
    pole.arrays = stoplightTemplate.arrays;
    pole.bufferInfo = stoplightTemplate.bufferInfo;
    pole.vao = stoplightTemplate.vao;
    pole.programInfo = colorProgramInfo;
    pole.scale = { x: 0.2, y: 0.8, z: 0.2 };
    pole.color = [0.3, 0.3, 0.3, 1.0];

    tl.visuals = { pole, lateralOffset };

    scene.addObject(pole);
  }
}

// ------------------- DRAW ONE OBJECT -------------------
function drawObject(
  gl,
  programInfo,
  object,
  viewProjectionMatrix,
  fract,
  timeMs
) {
  // Verificar si es un coche (está en el array agents) y aplicar offset en Y
  const isCar = agents.some((agent) => agent.id === object.id);
  // Las carreteras están en Y=0, los coches deben estar justo arriba
  const roadHeight = 0; // Altura de las carreteras
  const carHeightOffset = 0; // Offset para posicionar los coches sobre las carreteras

  if (object.isCheckpoint) {
    if (object.groundY === undefined) {
      object.groundY = object.position.y;
    }
    if (object.pulseOffset === undefined) {
      object.pulseOffset = Math.random() * Math.PI * 2;
    }
    const t = timeMs * 0.001;
    const bobOffset = 0.08 * Math.sin(t * 2.5 + object.pulseOffset);
    object.position.y = object.groundY + bobOffset;
  }

  // ========== EFECTOS DE CHOQUE ========== variables a consdieredsadfr
  let crashShakeX = 0;
  let crashShakeZ = 0;
  let crashRotX = 0;
  let crashRotZ = 0;
  let crashScaleMultiplier = 1.0;
  let isCrashed = false;

  if (isCar && object.crashed) {
    isCrashed = true;
    const t = timeMs * 0.001;
    const intensity = Math.max(0, 1 - (object.crash_timer / 10)); // Disminuye con el tiempo para continuar con ritmo anterior de coches hacia su ruta

    // Vibración/shake rápido
    crashShakeX = Math.sin(t * 20) * 0.08 * intensity;
    crashShakeZ = Math.cos(t * 25) * 0.08 * intensity;

    // Inclinación del coche (como si estuviera dañado)
    crashRotX = Math.sin(t * 3) * 0.15 * intensity;
    crashRotZ = Math.cos(t * 2.5) * 0.12 * intensity;

    // Escala pulsante (como si estuviera "rebotando")
    crashScaleMultiplier = 1.0 + Math.sin(t * 8) * 0.05 * intensity;
  }
  // =========================================

  let v3_tra = object.posArray;
  if (isCar) {
    const carPos = object.lerpPos || object.posArray;
    v3_tra = [
      carPos[0] + crashShakeX,
      roadHeight + carHeightOffset,
      carPos[2] + crashShakeZ
    ];
  }

  let v3_sca = object.scaArray.map(s => s * crashScaleMultiplier);

  const scaMat = M4.scale(v3_sca);
  const rotXMat = M4.rotationX(object.rotRad.x + crashRotX);

  const rotY = isCar && object.lerpRot !== undefined
    ? object.lerpRot
    : object.rotRad.y;
  const rotYMat = M4.rotationY(rotY);

  const rotZMat = M4.rotationZ(object.rotRad.z + crashRotZ);

  const traMat = M4.translation(v3_tra);

  let transforms = M4.identity();
  transforms = M4.multiply(scaMat, transforms);
  transforms = M4.multiply(rotXMat, transforms);
  transforms = M4.multiply(rotYMat, transforms);
  transforms = M4.multiply(rotZMat, transforms);
  transforms = M4.multiply(traMat, transforms);

  object.matrix = transforms;

  const wvpMat = M4.multiply(viewProjectionMatrix, transforms);

  let objectUniforms;

  if (programInfo === textureProgramInfo) {
    // Configurar iluminación múltiple con semáforos
    const worldInverseTranspose = M4.transpose(M4.inverse(transforms));
    const cameraPos = scene.camera.posArray;

    // Encontrar los 3 semáforos más cercanos (o rellenar con posiciones neutras)
    const lightPositions = [];
    const diffuseColors = [];
    const specularColors = [];

    // Obtener posición del objeto
    const objPos = v3_tra;

    // Calcular distancias a semáforos y checkpoints
    const maxRange = 12.0;
    const allLights = [];

    // Agregar semáforos como fuentes de luz
    tlights.forEach((tl) => {
      const tlPos = tl.posArray;
      const dx = tlPos[0] - objPos[0];
      const dz = tlPos[2] - objPos[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist <= maxRange) {
        allLights.push({
          position: [tlPos[0], tlPos[1] + 0.6, tlPos[2]],
          distance: dist,
          type: "traffic",
          state: tl.state,
        });
      }
    });

    // Agregar checkpoints como fuentes de luz azul
    destinations.forEach((dest) => {
      const destPos = dest.posArray;
      const dx = destPos[0] - objPos[0];
      const dz = destPos[2] - objPos[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist <= maxRange) {
        allLights.push({
          position: [destPos[0], destPos[1] + 0.2, destPos[2]],
          distance: dist,
          type: "checkpoint",
        });
      }
    });


    // Agregar coches como fuentes de luz blanca
    agents.forEach((car) => {
      const carPos = car.lerpPos || car.posArray;
      const dx = carPos[0] - objPos[0];
      const dz = carPos[2] - objPos[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist <= maxRange && dist > 0.1) {
        // No iluminarse a sí mismo
        allLights.push({
          position: [carPos[0], 0.1, carPos[2]], // Luz por debajo del coche
          distance: dist,
          type: "car",
        });
      }
    });

    // Ordenar por distancia y tomar hasta 10 luces cercanas
    allLights.sort((a, b) => a.distance - b.distance);

    const numLights = Math.min(10, allLights.length);

    for (let i = 0; i < 10; i++) {
      if (i < allLights.length) {
        const light = allLights[i];
        lightPositions.push(...light.position);

        if (light.type === "checkpoint") {
          // Luz azul fosforescente para checkpoints
          diffuseColors.push(0.1, 0.8, 1.2, 1.0);
          specularColors.push(0.15, 1.0, 1.5, 1.0);

        } else if (light.type === "car") {
          // Luz blanca para coches
          diffuseColors.push(0.6, 0.6, 0.6, 1.0);
          specularColors.push(0.8, 0.8, 0.8, 1.0);

        } else {
          // Color según estado del semáforo
          if (light.state === "red") {
            diffuseColors.push(0.8, 0.0, 0.0, 1.0);
            specularColors.push(1.0, 0.0, 0.0, 1.0);
          } else if (light.state === "green") {
            diffuseColors.push(0.0, 0.8, 0.0, 1.0);
            specularColors.push(0.0, 1.0, 0.0, 1.0);
          } else {
            diffuseColors.push(0.8, 0.8, 0.0, 1.0);
            specularColors.push(1.0, 1.0, 0.0, 1.0);
          }
        }
      } else {
        lightPositions.push(0, 1000, 0);
        diffuseColors.push(0.0, 0.0, 0.0, 1.0);
        specularColors.push(0.0, 0.0, 0.0, 1.0);
      }
    }

    
    // Efecto de color para coches chocados
    let ambientLight;
    if (isCrashed) {
      const t = timeMs * 0.001;
      const flash = Math.abs(Math.sin(t * 6)); // Flash rápido
      const intensity = Math.max(0, 1 - (object.crash_timer / 10));
      const redBoost = flash * 0.6 * intensity;
      const orangeGreen = flash * 0.3 * intensity;

      ambientLight = [
        globalLightIntensity * 0.5 + redBoost,
        globalLightIntensity * 0.5 + orangeGreen * 0.5,
        globalLightIntensity * 0.5,
        1
      ];
    } else {
      ambientLight = [globalLightIntensity * 0.5, globalLightIntensity * 0.5, globalLightIntensity * 0.5, 1];
    }


    objectUniforms = {
      u_worldViewProjection: wvpMat,
      u_world: transforms,
      u_worldInverseTransform: worldInverseTranspose,
      u_lightWorldPosition: lightPositions,
      u_viewWorldPosition: cameraPos,
      u_shininess: object.shininess || 50,
      u_ambientLight: ambientLight,
      u_diffuseLight: diffuseColors,
      u_specularLight: specularColors,
      u_constant: 1.0,
      u_linear: 0.08,
      u_quadratic: 0.06,
      u_texture: object.texture || null,
    };
  } else {
    objectUniforms = {
      u_transforms: wvpMat,
      ucolor: object.color,
      u_lightIntensity: globalLightIntensity,
    };
  }

  const enableBeamBlend = !!object.isCheckpoint;
  if (enableBeamBlend) {
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
    gl.depthMask(false);
  }

  twgl.setUniforms(programInfo, objectUniforms);

  gl.bindVertexArray(object.vao);
  twgl.drawBufferInfo(gl, object.bufferInfo);

  if (enableBeamBlend) {
    gl.disable(gl.BLEND);
    gl.depthMask(true);
  }
}

// ------------------- MAIN LOOP -------------------
async function drawScene() {
  let now = Date.now();
  let deltaTime = now - then;
  elapsed += deltaTime;
  let fract = Math.min(1.0, elapsed / duration);
  then = now;

  const bgColor = 0.2 * globalLightIntensity;
  gl.clearColor(bgColor, bgColor, bgColor, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  gl.disable(gl.CULL_FACE);
  gl.enable(gl.DEPTH_TEST);

  scene.camera.checkKeys();
  const viewProjectionMatrix = setupViewProjection(gl);

  // ----- Skybox -----
  // Render skybox first (it should follow the camera)
  gl.useProgram(skyboxProgramInfo.program);
  skybox.position.x = scene.camera.position.x;
  skybox.position.y = scene.camera.position.y;
  skybox.position.z = scene.camera.position.z;

  const skyboxScaMat = M4.scale(skybox.scaArray);
  const skyboxRotXMat = M4.rotationX(skybox.rotRad.x);
  const skyboxRotYMat = M4.rotationY(skybox.rotRad.y);
  const skyboxRotZMat = M4.rotationZ(skybox.rotRad.z);
  const skyboxTraMat = M4.translation(skybox.posArray);

  let skyboxTransforms = M4.identity();
  skyboxTransforms = M4.multiply(skyboxScaMat, skyboxTransforms);
  skyboxTransforms = M4.multiply(skyboxRotXMat, skyboxTransforms);
  skyboxTransforms = M4.multiply(skyboxRotYMat, skyboxTransforms);
  skyboxTransforms = M4.multiply(skyboxRotZMat, skyboxTransforms);
  skyboxTransforms = M4.multiply(skyboxTraMat, skyboxTransforms);

  const skyboxWvpMat = M4.multiply(viewProjectionMatrix, skyboxTransforms);

  const skyboxUniforms = {
    u_worldViewProjection: skyboxWvpMat,
    u_texture: skybox.texture,
    u_lightIntensity: 1.0,
  };

  twgl.setUniforms(skyboxProgramInfo, skyboxUniforms);
  gl.bindVertexArray(skybox.vao);
  twgl.drawBufferInfo(gl, skybox.bufferInfo);

  for (let i = scene.objects.length - 1; i >= 0; i--) {
    const obj = scene.objects[i];
    if (obj.isCar && !agents.some(agent => agent.id === obj.id)) {
      scene.objects.splice(i, 1);
    }
  }

  // Actualizar contadores
  if (window.guiSettings) {
    window.guiSettings.carsInMap = agents.length;
    window.guiSettings.currentStep = currentStep;
    window.guiSettings.totalCarsSpawned = carsSpawned;
    window.guiSettings.carsArrived = carsArrived;
  }

  // ----- Coches -----
  for (const agent of agents) {
    if (!agent.bufferInfo) {
      setupCarAgent(agent);
    }

    if (!agent.oldPos) {
      agent.oldPos = [...agent.posArray];
    }

    const pos = agent.posArray;
    const old = agent.oldPos;

    const dx = pos[0] - old[0];
    const dz = pos[2] - old[2];
    const dist = Math.sqrt(dx * dx + dz * dz);

    if (!agent.rotRad) {
      agent.rotRad = { x: 0, y: 0, z: 0 };
    }

    if (dist > 0.0001) {
      const ndx = dx / dist;
      const ndz = dz / dist;
      const angle = Math.acos(ndz);
      const target = ndx >= 0 ? angle : -angle;

      if (agent.oldRot === undefined) {
        agent.oldRot = agent.rotRad.y;
      }

      agent.targetRot = target;
    } else {
      if (agent.targetRot === undefined) {
        agent.targetRot = agent.rotRad.y;
      }
      if (agent.oldRot === undefined) {
        agent.oldRot = agent.rotRad.y;
      }
    }

    let r1 = agent.oldRot || 0;
    let r2 = agent.targetRot || 0;

    let diff = r2 - r1;
    if (diff > Math.PI) diff -= 2 * Math.PI;
    if (diff < -Math.PI) diff += 2 * Math.PI;

    agent.lerpRot = r1 + diff * fract;

    agent.lerpPos = [
      old[0] + (pos[0] - old[0]) * fract,
      old[1] + (pos[1] - old[1]) * fract,
      old[2] + (pos[2] - old[2]) * fract,
    ];

    if (agent.wheels) {
      const carPos = agent.lerpPos || agent.posArray;
      const carRotY = agent.lerpRot ?? agent.rotRad.y;

      const prevFramePos = agent.prevFramePos || carPos;
      const fx = carPos[0] - prevFramePos[0];
      const fz = carPos[2] - prevFramePos[2];
      const frameDist = Math.sqrt(fx * fx + fz * fz);
      const moving = frameDist > 0.00001;
      agent.prevFramePos = [...carPos];

      if (!agent.wheelRotX) {
        agent.wheelRotX = [0, 0, 0, 0];
      }

      const sinY = Math.sin(carRotY);
      const cosY = Math.cos(carRotY);

      const rollingFactor = 35.0;

      const roadHeight = 0;
      const carHeightOffset = 0;
      const baseY = roadHeight + carHeightOffset;

      gl.useProgram(textureProgramInfo.program);

      for (let i = 0; i < agent.wheels.length; i++) {
        const wheel = agent.wheels[i];

        if (moving) {
          agent.wheelRotX[i] += frameDist * rollingFactor;
        }

        const local = wheel.localOffset;
        const scale = agent.scale;
        const baseRotY = wheel.baseRotY || 0;

        // Calcular la rotación objetivo de la llanta
        const targetWheelRotY = carRotY + baseRotY;

        // Interpolar suavemente desde la rotación anterior (mismo método que el coche)
        if (wheel.currentRotY === undefined) {
          wheel.currentRotY = targetWheelRotY;
        }

        let diff = targetWheelRotY - wheel.currentRotY;
        // Manejar wraparound para tomar el camino más corto
        if (diff > Math.PI) diff -= 2 * Math.PI;
        if (diff < -Math.PI) diff += 2 * Math.PI;

        // Interpolar usando fract (la misma fracción que usa el coche)
        const interpolatedRotY = wheel.currentRotY + diff * fract;

        const scaledX = local[0] * scale.x;
        const scaledY = local[1] * scale.y;
        const scaledZ = local[2] * scale.z;

        // Aplicar rotación correcta alrededor del eje Y (antihoraria desde arriba) correción deJP a Juan de DIos
        const offsetX = scaledX * cosY + scaledZ * sinY;
        const offsetZ = -scaledX * sinY + scaledZ * cosY;

        const originWorldX = carPos[0] + offsetX;
        const originWorldY = baseY + scaledY;
        const originWorldZ = carPos[2] + offsetZ;

        const rotX = agent.wheelRotX[i];

        const renderWheel = {
          id: -1,
          posArray: [originWorldX, originWorldY, originWorldZ],
          scaArray: [scale.x, scale.y, scale.z],
          rotRad: {
            x: rotX,
            y: interpolatedRotY,
            z: 0,
          },
          arrays: wheel.arrays,
          bufferInfo: wheel.bufferInfo,
          vao: wheel.vao,
          programInfo: textureProgramInfo,
          texture: wheel.texture,
          color: wheel.color,
        };

        gl.useProgram(textureProgramInfo.program);

        drawObject(
          gl,
          textureProgramInfo,
          renderWheel,
          viewProjectionMatrix,
          fract,
          now
        );
      }
    }
  }

  // ----- Semáforos -----
  for (const tl of tlights) {
    if (!tl.visuals) continue;
    const { pole, lateralOffset } = tl.visuals;
    const pos = tl.posArray;

    const polePosX = pos[0] + lateralOffset;
    const polePosY = pos[1];
    const polePosZ = pos[2];

    pole.posArray[0] = polePosX;
    pole.posArray[1] = polePosY;
    pole.posArray[2] = polePosZ;
  }

  // ----- Dibujar todos los objetos de la escena -----
  for (let object of scene.objects) {
    const programInfo = object.programInfo || colorProgramInfo;
    gl.useProgram(programInfo.program);
    drawObject(gl, programInfo, object, viewProjectionMatrix, fract, now);
  }


  // ----- Avanzar el modelo de agentes -----
  if (elapsed >= duration) {

    elapsed = 0;

    // Guardar IDs antes de actualizar
    const agentIdsBefore = new Set(agents.map(a => a.id));

    for (const agent of agents) {
      if (agent.oldPos) {
        agent.oldPos = [...agent.posArray];
      }
      if (agent.targetRot !== undefined) {
        agent.oldRot = agent.targetRot;
      }
      // Actualizar rotación de las llantas
      if (agent.wheels) {
        const carRotY = agent.targetRot ?? agent.rotRad.y;
        for (const wheel of agent.wheels) {
          const baseRotY = wheel.baseRotY || 0;
          wheel.currentRotY = carRotY + baseRotY;
        }
      }
    }
    await update();

    // Detectar coches eliminados y quitarlos de la escena
    const agentIdsAfter = new Set(agents.map(a => a.id));
    const removedIds = [...agentIdsBefore].filter(id => !agentIdsAfter.has(id));

    if (removedIds.length > 0) {
      // Eliminar objetos de la escena que ya no están en agents
      scene.objects = scene.objects.filter(obj => !removedIds.includes(obj.id));
      console.log(`Removed ${removedIds.length} unit(s)`);
    }
  }

  requestAnimationFrame(drawScene);
}

// ------------------- CAMERA PROJECTION -------------------
function setupViewProjection(gl) {
  const fov = (60 * Math.PI) / 180;
  const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;

  const projectionMatrix = M4.perspective(fov, aspect, 1, 200);

  const cameraPosition = scene.camera.posArray;
  const target = scene.camera.targetArray;
  const up = [0, 1, 0];

  const cameraMatrix = M4.lookAt(cameraPosition, target, up);
  const viewMatrix = M4.inverse(cameraMatrix);
  const viewProjectionMatrix = M4.multiply(projectionMatrix, viewMatrix);

  return viewProjectionMatrix;
}

// ------------------- UI -------------------
function setupUI() {
  const gui = new GUI();

  const settings = {
    carSpawnRate: 5,
    borrachitoOn: false,
    carsInMap: 0,
    currentStep: 0,
    totalCarsSpawned: 0,
    carsArrived: 0,
    startSimulation: () => {
      if (!simulationStarted) {
        simulationStarted = true;
        isPaused = false;
        elapsed = 0;
        then = Date.now();
        console.log("Init");
      }
    },
    togglePause: () => {
      if (!simulationStarted) {
        console.log("Not started yet");
        return;
      }
      isPaused = !isPaused;
      console.log(isPaused ? "Paused" : "Resumed");
    },
    resetSimulation: () => {
      fetch("http://localhost:8585/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ NAgents: 20, width: 28, height: 28 })
      })
        .then((r) => r.json())
        .then((msg) => {
          console.log("Reset:", msg);
          window.location.reload();
        })
        .catch((err) => console.error(err));
    }
  };

  // Hacer settings accesible globalmente para actualizar contadores
  window.guiSettings = settings;

  const dataFolder = gui.addFolder("Datos");

  dataFolder
    .add(settings, "currentStep")
    .name("Step actual")
    .listen();

  dataFolder
    .add(settings, "carsInMap")
    .name("Coches en el mapa")
    .listen();

  dataFolder
    .add(settings, "totalCarsSpawned")
    .name("Coches totales spawneados")
    .listen();

  dataFolder
    .add(settings, "carsArrived")
    .name("Coches que llegaron")
    .listen();

  const simulationFolder = gui.addFolder("Simulación");

  simulationFolder
    .add(settings, "startSimulation")
    .name("Iniciar Simulación");

  simulationFolder
    .add(settings, "togglePause")
    .name("Pausar/Reanudar");

  simulationFolder
    .add(settings, "resetSimulation")
    .name("Reset Simulación");

  const logicFolder = gui.addFolder("Tráfico");

  logicFolder
    .add(settings, "borrachitoOn")
    .name("Modo Borrachito")
    .onChange((value) => {
      fetch("http://localhost:8585/setBorrachitoMode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ borrachitoOn: value }),
      })
        .then((r) => r.json())
        .then((msg) => console.log("Mode:", msg))
        .catch((err) => console.error(err));
    });

  logicFolder
    .add(settings, "carSpawnRate", 1, 50, 1)
    .name("Spawn cada N steps")
    .onChange((value) => {
      fetch("http://localhost:8585/setCarSpawnRate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rate: value }),
      })
        .then((r) => r.json())
        .then((msg) => console.log("Rate updated:", msg))
        .catch((err) => console.error(err));
    });
}

function parseAndCenterObj(text) {
  const positions = [];
  const texcoords = [];
  const normals = [];
  const finalVertices = [];
  const finalTexcoords = [];
  const finalNormals = [];

  const lines = text.split("\n");
  for (let line of lines) {
    line = line.trim();
    if (line.startsWith("v ")) {
      const parts = line.split(/\s+/);
      positions.push([
        parseFloat(parts[1]),
        parseFloat(parts[2]),
        parseFloat(parts[3]),
      ]);
    } else if (line.startsWith("vt ")) {
      const parts = line.split(/\s+/);
      texcoords.push([parseFloat(parts[1]), parseFloat(parts[2])]);
    } else if (line.startsWith("vn ")) {
      const parts = line.split(/\s+/);
      normals.push([
        parseFloat(parts[1]),
        parseFloat(parts[2]),
        parseFloat(parts[3]),
      ]);
    }
  }

  let minX = Infinity,
    maxX = -Infinity;
  let minY = Infinity,
    maxY = -Infinity;
  let minZ = Infinity,
    maxZ = -Infinity;

  positions.forEach((p) => {
    if (p[0] < minX) minX = p[0];
    if (p[0] > maxX) maxX = p[0];
    if (p[1] < minY) minY = p[1];
    if (p[1] > maxY) maxY = p[1];
    if (p[2] < minZ) minZ = p[2];
    if (p[2] > maxZ) maxZ = p[2];
  });

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const centerZ = (minZ + maxZ) / 2;

  for (let line of lines) {
    line = line.trim();
    if (line.startsWith("f ")) {
      const parts = line.split(/\s+/).slice(1);
      for (let i = 1; i < parts.length - 1; i++) {
        const indices = [parts[0], parts[i], parts[i + 1]];
        for (const idxStr of indices) {
          const idxParts = idxStr.split("/");
          const vIdx = parseInt(idxParts[0]) - 1;
          const tIdx = idxParts[1] ? parseInt(idxParts[1]) - 1 : -1;
          const nIdx = idxParts[2] ? parseInt(idxParts[2]) - 1 : -1;

          finalVertices.push(
            positions[vIdx][0] - centerX,
            positions[vIdx][1] - centerY,
            positions[vIdx][2] - centerZ
          );

          if (tIdx >= 0 && texcoords[tIdx])
            finalTexcoords.push(texcoords[tIdx][0], texcoords[tIdx][1]);
          else finalTexcoords.push(0, 0);

          if (nIdx >= 0 && normals[nIdx])
            finalNormals.push(
              normals[nIdx][0],
              normals[nIdx][1],
              normals[nIdx][2]
            );
          else finalNormals.push(0, 1, 0);
        }
      }
    }
  }

  return {
    a_position: { numComponents: 3, data: finalVertices },
    a_texcoord: { numComponents: 2, data: finalTexcoords },
    a_normal: { numComponents: 3, data: finalNormals },
  };
}

function computeObjCenter(text) {
  const positions = [];
  const lines = text.split("\n");
  for (let line of lines) {
    line = line.trim();
    if (line.startsWith("v ")) {
      const parts = line.split(/\s+/);
      positions.push([
        parseFloat(parts[1]),
        parseFloat(parts[2]),
        parseFloat(parts[3]),
      ]);
    }
  }

  let minX = Infinity,
    maxX = -Infinity;
  let minY = Infinity,
    maxY = -Infinity;
  let minZ = Infinity,
    maxZ = -Infinity;

  positions.forEach((p) => {
    if (p[0] < minX) minX = p[0];
    if (p[0] > maxX) maxX = p[0];
    if (p[1] < minY) minY = p[1];
    if (p[1] > maxY) maxY = p[1];
    if (p[2] < minZ) minZ = p[2];
    if (p[2] > maxZ) maxZ = p[2];
  });

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const centerZ = (minZ + maxZ) / 2;

  return [centerX, centerY, centerZ];
}

main();