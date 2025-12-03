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

// --------- TRAFFIC LIGHT ----------
import trafficLightModel from "../newAssets/signs/model.obj?raw";

// --------- ROADS ----------
import roadStraight from "../newAssets/roads/road-straight.obj?raw";

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

let stoplightTemplate = undefined;

let roadTexture = undefined;
let roadStraightTemplate = undefined;

let skybox = undefined;
let skyboxTexture2D = undefined;

let gl = undefined;
const duration = 1000;
let elapsed = 0;
let then = 0;
let baseCube = undefined;
let checkpointTemplate = undefined;
let globalLightIntensity = 0.5;

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

  roadTexture = twgl.createTexture(gl, {
    min: gl.NEAREST,
    mag: gl.NEAREST,
    src: roadsColormap,
    flipY: true,
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
  drawScene();
}

// ------------------- SCENE SETUP -------------------
function setupScene() {
  let camera = new Camera3D(
    0,
    10, 
    4, 
    0.8,
    [0, 0, 10],
    [0, 0, 0]
  );

  camera.panOffset = [0, 8, 0];
  scene.setCamera(camera);
  scene.camera.setupControls();

  scene.addLight(new Object3D(0, [100, 100, 100], [1, 1, 1]));
}

// ------------------- CAR SETUP -------------------
function setupCarAgent(agent) {
  const index = Math.floor(Math.random() * carBodyTemplates.length);
  const bodyTemplate = carBodyTemplates[index];

  agent.arrays = bodyTemplate.arrays;
  agent.bufferInfo = bodyTemplate.bufferInfo;
  agent.vao = bodyTemplate.vao;
  agent.programInfo = textureProgramInfo;
  agent.texture = carTexture;
  agent.scale = { x: 0.35, y: 0.35, z: 0.35 };
  agent.color = [1, 1, 1, 1];
  agent.isCar = true;

  if (!agent.rotRad) {
    agent.rotRad = { x: 0, y: 0, z: 0 };
  }
  if (!agent.prevPos) {
    agent.prevPos = [...agent.posArray];
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
         0.0,  0.0,  0.0,
        // Base triangle (hovering above)
        -0.35, 0.6, -0.28,
         0.35, 0.6, -0.28,
         0.0,  0.6,  0.42,
      ],
    },
    indices: {
      numComponents: 3,
      data: [
        0, 1, 2,
        0, 2, 3,
        0, 3, 1,
        1, 3, 2,
      ],
    },
  };
  checkpointTemplate.arrays = checkpointArrays;
  checkpointTemplate.bufferInfo = twgl.createBufferInfoFromArrays(gl, checkpointArrays);
  checkpointTemplate.vao = twgl.createVAOFromBufferInfo(gl, colorProgramInfo, checkpointTemplate.bufferInfo);
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

  // --- Plantilla de semáforo ---
  stoplightTemplate = new Object3D(-1);
  stoplightTemplate.prepareVAO(gl, colorProgramInfo, trafficLightModel);

  // --- Plantilla de carretera ---
  roadStraightTemplate = new Object3D(-1);
  roadStraightTemplate.prepareVAO(gl, textureProgramInfo, roadStraight);
  roadStraightTemplate.texture = roadTexture;

  // ---------- Obstáculos: edificios ----------
  for (const agent of obstacles) {
    const template =
      buildingTemplates[Math.floor(Math.random() * buildingTemplates.length)];
    agent.arrays = template.arrays;
    agent.bufferInfo = template.bufferInfo;
    agent.vao = template.vao;
    agent.programInfo = textureProgramInfo;
    agent.texture = buildingTexture;
    agent.scale = { x: 0.5, y: 0.5, z: 0.5 };
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

  // ---------- Calles: solo road-straight, sin orientación automática ----------
  for (const road of roads) {
    if (!road.rotRad) {
      road.rotRad = { x: 0, y: 0, z: 0 };
    }

    road.arrays = roadStraightTemplate.arrays;
    road.bufferInfo = roadStraightTemplate.bufferInfo;
    road.vao = roadStraightTemplate.vao;
    road.programInfo = textureProgramInfo;
    road.texture = roadTexture;
    road.scale = { x: 1.0, y: 1.0, z: 1.0 };
    road.color = [1, 1, 1, 1];
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
function drawObject(gl, programInfo, object, viewProjectionMatrix, fract, timeMs) {
  // Verificar si es un coche (está en el array agents) y aplicar offset en Y
  const isCar = agents.some(agent => agent.id === object.id);
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

  let v3_tra = object.posArray;
  if (isCar) {
    const carPos = object.lerpPos || object.posArray;
    v3_tra = [carPos[0], roadHeight + carHeightOffset, carPos[2]];
  }
  
  let v3_sca = object.scaArray;

  const scaMat = M4.scale(v3_sca);
  const rotXMat = M4.rotationX(object.rotRad.x);
  
  const rotY = isCar && object.lerpRot !== undefined 
    ? object.lerpRot 
    : object.rotRad.y;
  const rotYMat = M4.rotationY(rotY);
  
  const rotZMat = M4.rotationZ(object.rotRad.z);
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
    tlights.forEach(tl => {
      const tlPos = tl.posArray;
      const dx = tlPos[0] - objPos[0];
      const dz = tlPos[2] - objPos[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist <= maxRange) {
        allLights.push({
          position: [tlPos[0], tlPos[1] + 0.6, tlPos[2]],
          distance: dist,
          type: 'traffic',
          state: tl.state
        });
      }
    });
    
    // Agregar checkpoints como fuentes de luz azul
    destinations.forEach(dest => {
      const destPos = dest.posArray;
      const dx = destPos[0] - objPos[0];
      const dz = destPos[2] - objPos[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist <= maxRange) {
        allLights.push({
          position: [destPos[0], destPos[1] + 0.2, destPos[2]],
          distance: dist,
          type: 'checkpoint'
        });
      }
    });
    
    // Agregar coches como fuentes de luz blanca
    agents.forEach(car => {
      const carPos = car.lerpPos || car.posArray;
      const dx = carPos[0] - objPos[0];
      const dz = carPos[2] - objPos[2];
      const dist = Math.sqrt(dx * dx + dz * dz);
      if (dist <= maxRange && dist > 0.1) { // No iluminarse a sí mismo
        allLights.push({
          position: [carPos[0], 0.1, carPos[2]], // Luz por debajo del coche
          distance: dist,
          type: 'car'
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
        
        if (light.type === 'checkpoint') {
          // Luz azul fosforescente para checkpoints
          diffuseColors.push(0.1, 0.8, 1.2, 1.0);
          specularColors.push(0.15, 1.0, 1.5, 1.0);
        } else if (light.type === 'car') {
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
    
    objectUniforms = {
      u_worldViewProjection: wvpMat,
      u_world: transforms,
      u_worldInverseTransform: worldInverseTranspose,
      u_lightWorldPosition: lightPositions,
      u_viewWorldPosition: cameraPos,
      u_shininess: object.shininess || 50,
      u_ambientLight: [globalLightIntensity * 0.5, globalLightIntensity * 0.5, globalLightIntensity * 0.5, 1],
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
      old[2] + (pos[2] - old[2]) * fract
    ];
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

  if (elapsed >= duration) {
    elapsed = 0;
    for (const agent of agents) {
      if (agent.oldPos) {
        agent.oldPos = [...agent.posArray];
      }
      if (agent.targetRot !== undefined) {
        agent.oldRot = agent.targetRot;
      }
    }
    await update();
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
  };

  const logicFolder = gui.addFolder("Tráfico");

  logicFolder
    .add(settings, "borrachitoOn")
    .name("Modo Borrachito")
    .onChange((value) => {});

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
        .then((msg) => console.log("Spawn rate actualizado:", msg))
        .catch((err) => console.error(err));
    });
}

main();