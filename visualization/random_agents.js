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
import vsTextureGLSL from "../assets/shaders/vs_flat_textures.glsl?raw";
import fsTextureGLSL from "../assets/shaders/fs_flat_textures.glsl?raw";

const scene = new Scene3D();

// Global variables
let colorProgramInfo = undefined;
let textureProgramInfo = undefined;

let buildingTexture = undefined;
const buildingTemplates = [];

let carTexture = undefined;
const carBodyTemplates = [];

let stoplightTemplate = undefined;

let roadTexture = undefined;
let roadStraightTemplate = undefined;

let gl = undefined;
const duration = 1000; 
let elapsed = 0;
let then = 0;
let baseCube = undefined;

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
    agent.arrays = baseCube.arrays;
    agent.bufferInfo = baseCube.bufferInfo;
    agent.vao = baseCube.vao;
    agent.scale = { x: 0.5, y: 0.5, z: 0.5 };
    agent.color = [0, 0, 1, 1.0];
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

    const bulbOffset = { x: 0, y: 0.6, z: 0 };
    const bulbPos = [
      polePos[0] + bulbOffset.x,
      polePos[1] + bulbOffset.y,
      polePos[2] + bulbOffset.z,
    ];
    const bulb = new Object3D(-1, bulbPos);
    bulb.arrays = baseCube.arrays;
    bulb.bufferInfo = baseCube.bufferInfo;
    bulb.vao = baseCube.vao;
    bulb.programInfo = colorProgramInfo;
    bulb.scale = { x: 0.16, y: 0., z: 0.16 };
    if (tl.state === "red") bulb.color = [1, 0, 0, 1];
    else if (tl.state === "green") bulb.color = [0, 1, 0, 1];
    else bulb.color = [0.2, 0.2, 0.2, 1];

    tl.visuals = { pole, bulb, lateralOffset, bulbOffset };

    scene.addObject(pole);
    scene.addObject(bulb);
  }
}

// ------------------- DRAW ONE OBJECT -------------------
function drawObject(gl, programInfo, object, viewProjectionMatrix, fract) {
  // Verificar si es un coche (está en el array agents) y aplicar offset en Y
  const isCar = agents.some(agent => agent.id === object.id);
  // Las carreteras están en Y=0, los coches deben estar justo arriba
  const roadHeight = 0; // Altura de las carreteras
  const carHeightOffset = 0; // Offset para posicionar los coches sobre las carreteras
  
  let v3_tra = object.posArray;
  if (isCar) {
    // Los coches vienen con Y=1 del servidor, pero deben estar en Y=0.15 (arriba de la carretera)
    v3_tra = [v3_tra[0], roadHeight + carHeightOffset, v3_tra[2]];
  }
  
  let v3_sca = object.scaArray;

  const scaMat = M4.scale(v3_sca);
  const rotXMat = M4.rotationX(object.rotRad.x);
  const rotYMat = M4.rotationY(object.rotRad.y);
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
    objectUniforms = {
      u_worldViewProjection: wvpMat,
      ucolor: object.color,
      u_texture: object.texture || null,
    };
  } else {
    objectUniforms = {
      u_transforms: wvpMat,
      ucolor: object.color,
    };
  }

  twgl.setUniforms(programInfo, objectUniforms);

  gl.bindVertexArray(object.vao);
  twgl.drawBufferInfo(gl, object.bufferInfo);
}

// ------------------- MAIN LOOP -------------------
async function drawScene() {
  let now = Date.now();
  let deltaTime = now - then;
  elapsed += deltaTime;
  let fract = Math.min(1.0, elapsed / duration);
  then = now;

  gl.clearColor(0.2, 0.2, 0.2, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  gl.disable(gl.CULL_FACE);
  gl.enable(gl.DEPTH_TEST);

  scene.camera.checkKeys();
  const viewProjectionMatrix = setupViewProjection(gl);

  // ----- Coches -----
  for (const agent of agents) {
    if (!agent.bufferInfo) {
      setupCarAgent(agent);
    }

    if (!agent.prevPos) {
      agent.prevPos = [...agent.posArray];
    }

    const pos = agent.posArray;
    const prev = agent.prevPos;

    const dx = pos[0] - prev[0];
    const dz = pos[2] - prev[2];
    const dist = Math.hypot(dx, dz);

    if (!agent.rotRad) {
      agent.rotRad = { x: 0, y: 0, z: 0 };
    }

    if (dist > 0.0001) {
      const yaw = Math.atan2(dx, dz);
      agent.rotRad.y = yaw;
    }

    agent.prevPos[0] = pos[0];
    agent.prevPos[1] = pos[1];
    agent.prevPos[2] = pos[2];
  }

  // ----- Semáforos -----
  for (const tl of tlights) {
    if (!tl.visuals) continue;
    const { pole, bulb, lateralOffset, bulbOffset } = tl.visuals;
    const pos = tl.posArray;

    const polePosX = pos[0] + lateralOffset;
    const polePosY = pos[1];
    const polePosZ = pos[2];

    pole.posArray[0] = polePosX;
    pole.posArray[1] = polePosY;
    pole.posArray[2] = polePosZ;

    bulb.posArray[0] = polePosX + bulbOffset.x;
    bulb.posArray[1] = polePosY + bulbOffset.y;
    bulb.posArray[2] = polePosZ + bulbOffset.z;

    if (tl.state === "red") {
      bulb.color = [1, 0, 0, 1];
    } else if (tl.state === "green") {
      bulb.color = [0, 1, 0, 1];
    } else {
      bulb.color = [0.2, 0.2, 0.2, 1];
    }
  }

  // ----- Dibujar todos los objetos de la escena -----
  for (let object of scene.objects) {
    const programInfo = object.programInfo || colorProgramInfo;
    gl.useProgram(programInfo.program);
    drawObject(gl, programInfo, object, viewProjectionMatrix, fract);
  }

  if (elapsed >= duration) {
    elapsed = 0;
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
    camSpeed: 1.0,
    lightIntensity: 1.0,
    carSpawnRate: 5,
    borrachitoOn: false,
  };

  const camFolder = gui.addFolder("Cámara");
  camFolder
    .add(settings, "camSpeed", 0.1, 5.0, 0.1)
    .name("Velocidad cámara")
    .onChange((v) => {
      scene.camera.moveSpeed = v;
    });

  const lightFolder = gui.addFolder("Luz");
  lightFolder
    .add(settings, "lightIntensity", 0.1, 3.0, 0.1)
    .name("Intensidad luz")
    .onChange((v) => {
      if (scene.lights.length > 0) {
        scene.lights[0].intensity = v;
      }
    });

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