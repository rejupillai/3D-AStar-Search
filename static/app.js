/**
 * US Road Network Pathfinding Visualizer — Interactive ES6 SVG & 60fps Race Engine
 * Compares Standard Single-Source Dijkstra vs. Tri-Directional (3-Way Multi-Source) Search.
 */

const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
  nodes: [],
  edges: [],
  nodeById: new Map(),
  edgeById: new Map(),
  cityIndexByLabel: new Map(),

  // Active race payload from /api/race
  raceData: null,
  currentStepIndex: 0,
  maxSteps: 0,
  isPlaying: false,
  speedSeconds: 10, // Default 10 seconds to complete (30s on Slow Replay)
  layerMode: "both", // "both" | "tridir" | "dijkstra"
  rafId: null,
  raceStartTime: 0,
  lastFrameTime: 0,

  // DOM Lookup Caches
  nodeElements: new Map(),
  baseEdgeElements: new Map(),
};

// DOM References
const dom = {
  sourceSelect: document.getElementById("source-select"),
  hubSelect: document.getElementById("hub-select"),
  targetSelect: document.getElementById("target-select"),
  presetSelect: document.getElementById("preset-select"),

  startRaceBtn: document.getElementById("start-race-btn"),
  playPauseBtn: document.getElementById("play-pause-btn"),
  stepBtn: document.getElementById("step-btn"),
  resetBtn: document.getElementById("reset-btn"),
  speedSelect: document.getElementById("speed-select"),
  speedSlider: document.getElementById("speed-slider"),
  speedValue: document.getElementById("speed-value"),

  modeBtns: document.querySelectorAll(".layer-filter .chip"),

  // Scoreboard
  dijkstraStatus: document.getElementById("dijkstra-status"),
  dijkstraVisited: document.getElementById("dijkstra-visited"),
  dijkstraTime: document.getElementById("dijkstra-time"),
  dijkstraDistance: document.getElementById("dijkstra-distance"),

  tridirStatus: document.getElementById("tridir-status"),
  tridirVisited: document.getElementById("tridir-visited"),
  tridirSubcounts: document.getElementById("tridir-subcounts"),
  tridirTime: document.getElementById("tridir-time"),
  tridirDistance: document.getElementById("tridir-distance"),

  raceDeltaBadge: document.getElementById("race-delta-badge"),
  frameCounter: document.getElementById("frame-counter"),
  raceProgressFill: document.getElementById("race-progress-fill"),

  // SVG Layers
  layerBaseEdges: document.getElementById("layer-base-edges"),
  layerDijkstraEdges: document.getElementById("layer-dijkstra-edges"),
  layerTridirEdges: document.getElementById("layer-tridir-edges"),
  layerFinalPaths: document.getElementById("layer-final-paths"),
  layerNodes: document.getElementById("layer-nodes"),
  layerLabels: document.getElementById("layer-labels"),
  tooltip: document.getElementById("map-tooltip"),
  svgContainer: document.getElementById("svg-container"),

  // Live Data Structure Inspector
  inspectorStepBadge: document.getElementById("inspector-step-badge"),
  inspDPqLen: document.getElementById("insp-d-pq-len"),
  inspDPushesPops: document.getElementById("insp-d-pushes-pops"),
  inspDVisited: document.getElementById("insp-d-visited"),
  inspDCurrNode: document.getElementById("insp-d-curr-node"),
  inspDPqPreview: document.getElementById("insp-d-pq-preview"),
  inspDRelaxLog: document.getElementById("insp-d-relax-log"),

  inspTPqLen: document.getElementById("insp-t-pq-len"),
  inspTPushesPops: document.getElementById("insp-t-pushes-pops"),
  inspTHubName: document.getElementById("insp-t-hub-name"),
  inspTCurrNode: document.getElementById("insp-t-curr-node"),
  inspTPqPreview: document.getElementById("insp-t-pq-preview"),
  inspTRelaxLog: document.getElementById("insp-t-relax-log"),

  metaEdgeCount: document.getElementById("meta-edge-count"),
  metaAvgDeg: document.getElementById("meta-avg-deg"),
};

const PRESETS = {
  "la-ny": { source: "Los Angeles, CA", target: "New York, NY", hub: "auto" },
  "sea-mia": { source: "Seattle, WA", target: "Miami, FL", hub: "auto" },
  "sd-por": { source: "San Diego, CA", target: "Portland, ME", hub: "auto" },
  "sf-bos": { source: "San Francisco, CA", target: "Boston, MA", hub: "auto" },
  "anc-key": { source: "Anchorage, AK", target: "Key West, FL", hub: "auto" },
  "hnl-chi": { source: "Honolulu, HI", target: "Chicago, IL", hub: "auto" },
};

/**
 * Fetches the 336-city US road network graph and initializes selectors + SVG canvas.
 */
async function initVisualizer() {
  const res = await fetch("/api/graph");
  const data = await res.json();

  state.nodes = data.nodes;
  state.edges = data.edges;

  state.nodes.forEach((n) => {
    state.nodeById.set(n.id, n);
    state.cityIndexByLabel.set(n.label, n.id);
  });
  state.edges.forEach((e) => {
    state.edgeById.set(e.id, e);
  });

  if (data.stats) {
    dom.metaEdgeCount.textContent = `${data.stats.edge_count} Road Edges`;
    dom.metaAvgDeg.textContent = `Avg Degree: ${data.stats.avg_degree}`;
  }

  populateCityDropdowns();
  renderBaseGraphSVG();
  applyPreset("la-ny");
  bindEvents();
}

function populateCityDropdowns() {
  const sortedCities = [...state.nodes].sort((a, b) =>
    a.label.localeCompare(b.label)
  );

  const srcFrag = document.createDocumentFragment();
  const hubFrag = document.createDocumentFragment();
  const dstFrag = document.createDocumentFragment();

  sortedCities.forEach((city) => {
    const optS = document.createElement("option");
    optS.value = String(city.id);
    optS.textContent = `${city.label}`;
    srcFrag.appendChild(optS);

    const optH = document.createElement("option");
    optH.value = String(city.id);
    optH.textContent = `${city.label}`;
    hubFrag.appendChild(optH);

    const optT = document.createElement("option");
    optT.value = String(city.id);
    optT.textContent = `${city.label}`;
    dstFrag.appendChild(optT);
  });

  dom.sourceSelect.appendChild(srcFrag);
  dom.hubSelect.appendChild(hubFrag);
  dom.targetSelect.appendChild(dstFrag);
}

function applyPreset(presetKey) {
  const preset = PRESETS[presetKey];
  if (!preset) return;
  const sId = state.cityIndexByLabel.get(preset.source);
  const tId = state.cityIndexByLabel.get(preset.target);
  if (sId !== undefined) dom.sourceSelect.value = String(sId);
  if (tId !== undefined) dom.targetSelect.value = String(tId);
  dom.hubSelect.value = preset.hub;
  highlightSelectedPins();
}

function renderBaseGraphSVG() {
  dom.layerBaseEdges.innerHTML = "";
  dom.layerNodes.innerHTML = "";
  state.baseEdgeElements.clear();
  state.nodeElements.clear();

  const edgeFrag = document.createDocumentFragment();
  for (const edge of state.edges) {
    const u = state.nodeById.get(edge.source);
    const v = state.nodeById.get(edge.target);
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", String(u.svg_x));
    line.setAttribute("y1", String(u.svg_y));
    line.setAttribute("x2", String(v.svg_x));
    line.setAttribute("y2", String(v.svg_y));
    line.setAttribute(
      "class",
      edge.is_inset_link ? "base-edge inset-link" : "base-edge"
    );
    edgeFrag.appendChild(line);
    state.baseEdgeElements.set(edge.id, line);
  }
  dom.layerBaseEdges.appendChild(edgeFrag);

  const nodeFrag = document.createDocumentFragment();
  for (const city of state.nodes) {
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", String(city.svg_x));
    circle.setAttribute("cy", String(city.svg_y));
    circle.setAttribute("r", "3.4");
    circle.setAttribute("class", "city-node");
    circle.dataset.cityId = String(city.id);

    circle.addEventListener("mouseenter", (ev) => showCityTooltip(ev, city));
    circle.addEventListener("mouseleave", hideCityTooltip);
    circle.addEventListener("click", () => handleCityNodeClick(city.id));

    nodeFrag.appendChild(circle);
    state.nodeElements.set(city.id, circle);
  }
  dom.layerNodes.appendChild(nodeFrag);
}

function showCityTooltip(ev, city) {
  dom.tooltip.innerHTML = `<strong>${city.label}</strong><br/>Lat: ${city.latitude.toFixed(2)}° · Lon: ${city.longitude.toFixed(2)}°`;
  dom.tooltip.classList.remove("hidden");
  const rect = dom.svgContainer.getBoundingClientRect();
  const x = ev.clientX - rect.left + 12;
  const y = ev.clientY - rect.top - 12;
  dom.tooltip.style.left = `${x}px`;
  dom.tooltip.style.top = `${y}px`;
}

function hideCityTooltip() {
  dom.tooltip.classList.add("hidden");
}

function handleCityNodeClick(cityId) {
  // Cycle setting Origin or Destination on direct map click if not mid-race
  if (state.isPlaying) return;
  dom.targetSelect.value = String(cityId);
  highlightSelectedPins();
}

function highlightSelectedPins(resolvedHubId = null) {
  const sId = Number(dom.sourceSelect.value);
  const tId = Number(dom.targetSelect.value);
  const hVal = dom.hubSelect.value;
  const hId =
    resolvedHubId !== null
      ? resolvedHubId
      : hVal !== "auto"
      ? Number(hVal)
      : null;

  for (const [cid, el] of state.nodeElements.entries()) {
    el.classList.remove("pin-source", "pin-hub", "pin-target");
    el.setAttribute("r", "3.4");
    if (cid === sId) {
      el.classList.add("pin-source");
      el.setAttribute("r", "6.5");
    } else if (cid === tId) {
      el.classList.add("pin-target");
      el.setAttribute("r", "6.5");
    } else if (hId !== null && cid === hId) {
      el.classList.add("pin-hub");
      el.setAttribute("r", "6.0");
    }
  }

  // Render pin text labels on SVG
  dom.layerLabels.innerHTML = "";
  const pinEntries = [
    { id: sId, tag: "S" },
    ...(hId !== null ? [{ id: hId, tag: "M" }] : []),
    { id: tId, tag: "T" },
  ];

  for (const pin of pinEntries) {
    const city = state.nodeById.get(pin.id);
    if (!city) continue;
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", String(city.svg_x + 8));
    text.setAttribute("y", String(city.svg_y - 7));
    text.setAttribute("class", "pin-label");
    text.textContent = `[${pin.tag}] ${city.label}`;
    dom.layerLabels.appendChild(text);
  }
}

/**
 * Starts a synchronized pathfinding competition between Dijkstra and Tri-Directional Search.
 */
async function startRace() {
  stopAnimationLoop();

  const sourceId = Number(dom.sourceSelect.value);
  const targetId = Number(dom.targetSelect.value);
  const hubVal = dom.hubSelect.value;

  dom.startRaceBtn.disabled = true;
  dom.dijkstraStatus.textContent = "Computing...";
  dom.tridirStatus.textContent = "Computing...";

  try {
    const res = await fetch("/api/race", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_id: sourceId,
        target_id: targetId,
        hub_id: hubVal,
      }),
    });
    const data = await res.json();
    state.raceData = data;
    state.currentStepIndex = 0;
    state.maxSteps = Math.max(
      data.dijkstra.steps.length,
      data.tridirectional.steps.length
    );

    // Highlight S, resolved Hub M, and T
    highlightSelectedPins(data.tridirectional.hub_id);
    dom.inspTHubName.textContent = `${data.tridirectional.hub_label} (${data.tridirectional.hub_mode})`;

    clearTraversalLayers();

    state.isPlaying = true;
    dom.playPauseBtn.disabled = false;
    dom.playPauseBtn.textContent = "Pause";
    dom.dijkstraStatus.textContent = "Expanding...";
    dom.tridirStatus.textContent = "Expanding 3 Frontiers...";

    state.raceStartTime = performance.now();
    state.lastFrameTime = state.raceStartTime;
    state.rafId = requestAnimationFrame(animationTick);
  } catch (err) {
    console.error("Failed to execute race:", err);
  } finally {
    dom.startRaceBtn.disabled = false;
  }
}

function clearTraversalLayers() {
  dom.layerDijkstraEdges.innerHTML = "";
  dom.layerTridirEdges.innerHTML = "";
  dom.layerFinalPaths.innerHTML = "";
  for (const el of state.nodeElements.values()) {
    el.classList.remove(
      "visited-dijkstra",
      "visited-S",
      "visited-M",
      "visited-T"
    );
  }
}

function stopAnimationLoop() {
  if (state.rafId !== null) {
    cancelAnimationFrame(state.rafId);
    state.rafId = null;
  }
  state.isPlaying = false;
}

function setSpeedSeconds(sec) {
  const cleanSec = Math.max(5, Math.min(30, Number(sec) || 10));
  const oldSec = state.speedSeconds;
  state.speedSeconds = cleanSec;
  dom.speedSlider.value = String(cleanSec);
  dom.speedValue.textContent = `${cleanSec}s`;
  if (dom.speedSelect) {
    const matchingOption = Array.from(dom.speedSelect.options).find(
      (opt) => Number(opt.value) === cleanSec
    );
    if (matchingOption) {
      dom.speedSelect.value = matchingOption.value;
    }
  }
  // If currently playing, smoothly re-anchor raceStartTime so the remaining steps pace at the new speed
  if (state.isPlaying && state.maxSteps > 0 && oldSec !== cleanSec) {
    const frac = state.currentStepIndex / state.maxSteps;
    const targetDurationMs = cleanSec * 1000;
    state.raceStartTime = performance.now() - frac * targetDurationMs;
  }
}

function animationTick(now) {
  if (!state.isPlaying || !state.raceData) return;

  // Target total race duration in milliseconds directly from state.speedSeconds (e.g. 10s = 10,000ms, 30s = 30,000ms)
  const targetDurationMs = state.speedSeconds * 1000;
  const elapsedTotal = now - state.raceStartTime;
  const targetStep = Math.min(
    state.maxSteps,
    Math.max(1, Math.floor((elapsedTotal / targetDurationMs) * state.maxSteps))
  );

  if (targetStep > state.currentStepIndex) {
    state.currentStepIndex = targetStep;
    renderRaceFrame(state.currentStepIndex);
    state.lastFrameTime = now;
  }

  if (state.currentStepIndex < state.maxSteps) {
    state.rafId = requestAnimationFrame(animationTick);
  } else {
    finishRaceAnimation();
  }
}

/**
 * Renders the exact state of both algorithms at stepIndex (1..maxSteps).
 * Synchronizes both algorithms and their Live Data Structure Inspectors across the full duration
 * so both wavefronts and priority queue panels advance smoothly side-by-side over the chosen seconds.
 */
function renderRaceFrame(stepIndex) {
  if (!state.raceData) return;

  const dSteps = state.raceData.dijkstra.steps;
  const tSteps = state.raceData.tridirectional.steps;

  const progressFrac = state.maxSteps > 0 ? stepIndex / state.maxSteps : 0;
  const dCount = dSteps.length > 0 ? Math.max(1, Math.round(progressFrac * dSteps.length)) : 0;
  const tCount = tSteps.length > 0 ? Math.max(1, Math.round(progressFrac * tSteps.length)) : 0;

  const dIdx = Math.min(dCount, dSteps.length) - 1;
  const tIdx = Math.min(tCount, tSteps.length) - 1;

  const dStep = dIdx >= 0 ? dSteps[dIdx] : null;
  const tStep = tIdx >= 0 ? tSteps[tIdx] : null;

  // Update Progress Bar & Step Counter
  const pct = state.maxSteps > 0 ? Math.round((stepIndex / state.maxSteps) * 100) : 0;
  dom.frameCounter.textContent = `Step ${stepIndex} / ${state.maxSteps}`;
  dom.raceProgressFill.style.width = `${pct}%`;
  dom.inspectorStepBadge.textContent = `STEP ${stepIndex}`;

  // Clear and redraw active traversal layers up to stepIndex
  dom.layerDijkstraEdges.innerHTML = "";
  dom.layerTridirEdges.innerHTML = "";

  // Reset visited node classes before painting current snapshot
  for (const el of state.nodeElements.values()) {
    el.classList.remove(
      "visited-dijkstra",
      "visited-S",
      "visited-M",
      "visited-T"
    );
  }

  // 1. Render Dijkstra Wavefront (Amber/Yellow pulsing stroke)
  if (state.layerMode === "both" || state.layerMode === "dijkstra") {
    const dFrag = document.createDocumentFragment();
    for (let i = 0; i <= dIdx; i++) {
      const s = dSteps[i];
      const nodeEl = state.nodeElements.get(s.current_node);
      if (nodeEl) nodeEl.classList.add("visited-dijkstra");

      if (s.tree_edge !== null && s.tree_edge !== undefined) {
        const line = createEdgeLine(s.tree_edge, "edge-dijkstra-tree");
        if (line) dFrag.appendChild(line);
      }
    }
    // Pulsing frontier edges on current Dijkstra step
    if (dStep && dStep.active_edges) {
      for (const eid of dStep.active_edges) {
        const pulseLine = createEdgeLine(eid, "edge-dijkstra-active");
        if (pulseLine) dFrag.appendChild(pulseLine);
      }
    }
    dom.layerDijkstraEdges.appendChild(dFrag);
  }

  // 2. Render Tri-Directional 3-Way Frontiers (S: Neon Blue, M: Neon Purple, T: Neon Green)
  if (state.layerMode === "both" || state.layerMode === "tridir") {
    const tFrag = document.createDocumentFragment();
    for (let i = 0; i <= tIdx; i++) {
      const s = tSteps[i];
      const fKey = s.frontier; // "S" | "M" | "T"
      const nodeEl = state.nodeElements.get(s.current_node);
      if (nodeEl) nodeEl.classList.add(`visited-${fKey}`);

      if (s.tree_edge !== null && s.tree_edge !== undefined) {
        const line = createEdgeLine(s.tree_edge, `edge-tridir-${fKey}`);
        if (line) tFrag.appendChild(line);
      }
    }
    // Active blinking frontier edges on current Tri-Directional step
    if (tStep && tStep.active_edges) {
      for (const eid of tStep.active_edges) {
        const blinkLine = createEdgeLine(
          eid,
          `edge-tridir-active-${tStep.frontier}`
        );
        if (blinkLine) tFrag.appendChild(blinkLine);
      }
    }
    dom.layerTridirEdges.appendChild(tFrag);
  }

  // 3. Update Live Scoreboard & Data Structure Inspector
  updateInspectorAndScoreboard(dStep, tStep, stepIndex >= state.maxSteps);
}

function createEdgeLine(edgeId, className) {
  const edge = state.edgeById.get(edgeId);
  if (!edge) return null;
  const u = state.nodeById.get(edge.source);
  const v = state.nodeById.get(edge.target);
  const line = document.createElementNS(SVG_NS, "line");
  line.setAttribute("x1", String(u.svg_x));
  line.setAttribute("y1", String(u.svg_y));
  line.setAttribute("x2", String(v.svg_x));
  line.setAttribute("y2", String(v.svg_y));
  line.setAttribute("class", className);
  return line;
}

function updateInspectorAndScoreboard(dStep, tStep, isFinished) {
  const { dijkstra, tridirectional, comparison } = state.raceData;

  if (dStep) {
    dom.dijkstraVisited.innerHTML = `${dStep.visited_count} <small>/ 336</small>`;
    dom.inspDPqLen.textContent = String(dStep.pq_size);
    dom.inspDPushesPops.textContent = `${dStep.heap_pushes} / ${dStep.heap_pops}`;
    dom.inspDVisited.textContent = `${dStep.visited_count} nodes`;
    dom.inspDCurrNode.textContent = `${dStep.current_label} (${dStep.current_dist} mi)`;

    // Priority Queue Head Pills
    if (dStep.pq_preview && dStep.pq_preview.length > 0) {
      dom.inspDPqPreview.innerHTML = dStep.pq_preview
        .map(
          (item) =>
            `<span class="heap-pill">${item.label}: ${item.dist} mi</span>`
        )
        .join("");
    } else {
      dom.inspDPqPreview.innerHTML = `<span class="empty-note">Heap exhausted / target reached</span>`;
    }

    // Relaxation Log
    if (dStep.relaxations && dStep.relaxations.length > 0) {
      dom.inspDRelaxLog.innerHTML = dStep.relaxations
        .map(
          (r) =>
            `<li>${r.from} → <strong>${r.to}</strong>: ${r.old_dist} → ${r.new_dist} mi</li>`
        )
        .join("");
    }
  }

  if (tStep) {
    const fc = tStep.frontier_counts || { S: 0, M: 0, T: 0 };
    dom.tridirVisited.innerHTML = `${tStep.visited_count} <small id="tridir-subcounts">(${fc.S} | ${fc.M} | ${fc.T})</small>`;

    const pqs = tStep.pq_sizes || { S: 0, M: 0, T: 0 };
    dom.inspTPqLen.innerHTML = `${tStep.pq_size} <small>(${pqs.S}|${pqs.M}|${pqs.T})</small>`;
    dom.inspTPushesPops.textContent = `${tStep.heap_pushes} / ${tStep.heap_pops}`;
    dom.inspTCurrNode.textContent = `[${tStep.frontier}] ${tStep.current_label} (f=${tStep.current_f ?? tStep.current_dist} mi)`;

    if (tStep.pq_preview && tStep.pq_preview.length > 0) {
      dom.inspTPqPreview.innerHTML = tStep.pq_preview
        .map(
          (item) =>
            `<span class="heap-pill f-${item.frontier}">[${item.frontier}] ${item.label}: f=${item.dist} (g=${item.g}, h=${item.h})</span>`
        )
        .join("");
    }

    if (tStep.relaxations && tStep.relaxations.length > 0) {
      dom.inspTRelaxLog.innerHTML = tStep.relaxations
        .map(
          (r) =>
            `<li>[${r.frontier}] ${r.from} → <strong>${r.to}</strong>: g=${r.new_dist} + h=${r.h_val} ⇒ f=${r.f_val} mi</li>`
        )
        .join("");
    }
  }

  if (isFinished) {
    dom.dijkstraTime.textContent = `${dijkstra.execution_time_ms.toFixed(3)} ms`;
    dom.dijkstraDistance.textContent = `${dijkstra.final_distance_miles.toLocaleString()} mi`;
    dom.dijkstraStatus.textContent = "Target Reached ✓";

    dom.tridirTime.textContent = `${tridirectional.execution_time_ms.toFixed(3)} ms`;
    dom.tridirDistance.textContent = `${tridirectional.final_distance_miles.toLocaleString()} mi`;
    dom.tridirStatus.textContent = "3D A* Converged ✓";

    const red = comparison.node_reduction_pct;
    dom.raceDeltaBadge.textContent =
      red > 0
        ? `3D A* Visited ${red}% Fewer Cities (${tridirectional.visited_count} vs ${dijkstra.visited_count})`
        : `Race Complete (${tridirectional.visited_count} vs ${dijkstra.visited_count} nodes)`;
  } else {
    const dProgressRatio = dStep ? dStep.step / dijkstra.steps.length : 0;
    const tProgressRatio = tStep ? tStep.step / tridirectional.steps.length : 0;
    dom.dijkstraTime.textContent = `${(dijkstra.execution_time_ms * dProgressRatio).toFixed(3)} ms`;
    dom.tridirTime.textContent = `${(tridirectional.execution_time_ms * tProgressRatio).toFixed(3)} ms`;
    dom.raceDeltaBadge.textContent = `Racing: 3D A* ${tStep ? tStep.visited_count : 0} vs Dijkstra ${dStep ? dStep.visited_count : 0} nodes`;
  }
}

function finishRaceAnimation() {
  stopAnimationLoop();
  dom.playPauseBtn.textContent = "Slow Replay (30s)";
  dom.inspectorStepBadge.textContent = "COMPLETE";
  renderFinalShortestPaths();
}

function renderFinalShortestPaths() {
  if (!state.raceData) return;
  dom.layerFinalPaths.innerHTML = "";
  const frag = document.createDocumentFragment();

  if (state.layerMode === "both" || state.layerMode === "dijkstra") {
    for (const eid of state.raceData.dijkstra.path_edges) {
      const line = createEdgeLine(eid, "final-path-dijkstra");
      if (line) frag.appendChild(line);
    }
  }

  if (state.layerMode === "both" || state.layerMode === "tridir") {
    for (const eid of state.raceData.tridirectional.path_edges) {
      const glowLine = createEdgeLine(eid, "final-path-tridir");
      const coreLine = createEdgeLine(eid, "final-path-tridir-core");
      if (glowLine) frag.appendChild(glowLine);
      if (coreLine) frag.appendChild(coreLine);
    }
  }

  dom.layerFinalPaths.appendChild(frag);
}

function bindEvents() {
  dom.startRaceBtn.addEventListener("click", () => startRace());

  dom.playPauseBtn.addEventListener("click", () => {
    if (!state.raceData) return;
    if (state.currentStepIndex >= state.maxSteps) {
      // Slow Replay from step 0 at 30s speed
      setSpeedSeconds(30);
      state.currentStepIndex = 0;
      dom.layerFinalPaths.innerHTML = "";
      state.isPlaying = true;
      dom.playPauseBtn.textContent = "Pause";
      state.raceStartTime = performance.now();
      state.lastFrameTime = state.raceStartTime;
      state.rafId = requestAnimationFrame(animationTick);
      return;
    }

    if (state.isPlaying) {
      stopAnimationLoop();
      dom.playPauseBtn.textContent = "Play";
    } else {
      state.isPlaying = true;
      dom.playPauseBtn.textContent = "Pause";
      const targetDurationMs = state.speedSeconds * 1000;
      const frac = state.maxSteps > 0 ? state.currentStepIndex / state.maxSteps : 0;
      state.raceStartTime = performance.now() - frac * targetDurationMs;
      state.lastFrameTime = performance.now();
      state.rafId = requestAnimationFrame(animationTick);
    }
  });

  dom.stepBtn.addEventListener("click", async () => {
    if (!state.raceData) {
      await startRace();
      stopAnimationLoop();
      dom.playPauseBtn.textContent = "Play";
      state.currentStepIndex = 1;
      renderRaceFrame(1);
      return;
    }
    stopAnimationLoop();
    dom.playPauseBtn.textContent = "Play";
    if (state.currentStepIndex < state.maxSteps) {
      state.currentStepIndex += 1;
      renderRaceFrame(state.currentStepIndex);
      if (state.currentStepIndex >= state.maxSteps) {
        finishRaceAnimation();
      }
    }
  });

  dom.resetBtn.addEventListener("click", () => {
    stopAnimationLoop();
    state.raceData = null;
    state.currentStepIndex = 0;
    state.maxSteps = 0;
    clearTraversalLayers();
    highlightSelectedPins();
    dom.playPauseBtn.disabled = true;
    dom.playPauseBtn.textContent = "Pause";
    dom.frameCounter.textContent = "Step 0 / 0";
    dom.raceProgressFill.style.width = "0%";
    dom.raceDeltaBadge.textContent = "Awaiting Race Start";
    dom.inspectorStepBadge.textContent = "IDLE";
  });

  dom.speedSlider.addEventListener("input", () => {
    setSpeedSeconds(Number(dom.speedSlider.value));
  });

  if (dom.speedSelect) {
    dom.speedSelect.addEventListener("change", () => {
      setSpeedSeconds(Number(dom.speedSelect.value));
    });
  }

  dom.presetSelect.addEventListener("change", () => {
    applyPreset(dom.presetSelect.value);
  });

  dom.sourceSelect.addEventListener("change", () => highlightSelectedPins());
  dom.hubSelect.addEventListener("change", () => highlightSelectedPins());
  dom.targetSelect.addEventListener("change", () => highlightSelectedPins());

  dom.modeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      dom.modeBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.layerMode = btn.dataset.mode;
      if (state.raceData) {
        renderRaceFrame(state.currentStepIndex);
        if (state.currentStepIndex >= state.maxSteps) {
          renderFinalShortestPaths();
        }
      }
    });
  });
}

initVisualizer();
