# Agent Visualization using WebGL  

This project demonstrates how to visualize agents from Mesa using WebGL. It uses two servers: a Python backend that runs the Mesa model through Flask, and a Vite server that hosts the WebGL-based visualization. Originally designed for Random Agents, the logic has been extended to support a Traffic/City simulation with vehicles, traffic lights, obstacles and destinations, allowing to observe the movement and the interaction of multiple agents in real time.

---

## Prerequisites

To run this visualization, you need two components running simultaneously:

1. **The Python Backend** — Mesa model exposed through Flask.
2. **The Web Frontend** — Served locally using Vite.

---

## Instructions to run the local server and the application

### 🛠️ Step 1: Start the Python Backend

1. Open a terminal at the root of the repository.
2. Activate your Python environment:

  
# Windows  
```bash
.\.agents\Scripts\Activate
```

# macOS / Linux  
```bash
source .agents/bin/activate  
```

3. Navigate to the `Server/agentsServer` folder.
4. Run the Flask server:

```bash  
python3 agents_server.py  
```


---

### 🚀 Step 2: Run the WebGL Visualization (Frontend)

1. Install dependencies (only once):

```bash  
npm i  
```

2. Start the Vite server:

```bash  
npx vite  
```

If everything is running correctly, visit:

```bash  
http://localhost:5173/visualizations/index.html  
```

You should now see the 3D scene rendered in WebGL showing moving agents.

---

## 🚦 Traffic Simulation Mode

This project now supports a Traffic Multi-Agent Simulation where cars navigate through a city grid with roads, traffic lights, obstacles and dynamic behaviors. Some agents may even act erratically (e.g., *Borrachito*) to stress-test the system.

To run this mode:

- Keep the backend running as shown above.
- Start the frontend with `npx vite`.
- Access the same visualization URL.

---

### ✔️ Ready to Explore

Once both servers are active, you can observe agents moving, reacting to traffic lights, avoiding obstacles and making route decisions. The visualization acts as an interactive window into the Mesa simulation.


