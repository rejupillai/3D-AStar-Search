"""FastAPI backend serving the 336-city US road network, pathfinding race API, and WebSocket stream."""

from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.algorithms import run_dijkstra, run_tridirectional_search
from app.graph_builder import build_us_road_network

app = FastAPI(
    title="US Road Network Pathfinding Visualizer",
    description="Comparing Standard Single-Source Dijkstra vs. 3-Directional A* (3-Way Heuristic) Search across 336 US cities.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-build the 336-city US road network graph at startup
ROAD_GRAPH: dict[str, Any] = build_us_road_network(k_neighbors=4)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class RaceRequest(BaseModel):
    source_id: int
    target_id: int
    hub_id: int | str | None = "auto"


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for Cloud Run and readiness probes."""
    return {
        "status": "ok",
        "service": "us-road-pathfinding-visualizer",
        "stats": ROAD_GRAPH["stats"],
    }


@app.get("/api/graph")
async def get_graph() -> dict[str, Any]:
    """Returns the 336 US cities, Albers USA coordinates, and Delaunay + k-NN road network edges."""
    return {
        "nodes": ROAD_GRAPH["nodes"],
        "edges": ROAD_GRAPH["edges"],
        "stats": ROAD_GRAPH["stats"],
    }


@app.post("/api/race")
async def execute_race(req: RaceRequest) -> dict[str, Any]:
    """Runs both Standard Dijkstra and Tri-Directional Search and returns step-by-step snapshots."""
    n = ROAD_GRAPH["stats"]["node_count"]
    if not (0 <= req.source_id < n) or not (0 <= req.target_id < n):
        raise HTTPException(status_code=400, detail="City ID out of range (0..335).")

    dijkstra_res = run_dijkstra(ROAD_GRAPH, req.source_id, req.target_id)
    tridir_res = run_tridirectional_search(
        ROAD_GRAPH, req.source_id, req.target_id, req.hub_id
    )

    d_vis = max(1, dijkstra_res["visited_count"])
    t_vis = tridir_res["visited_count"]
    node_reduction_pct = round(((d_vis - t_vis) / d_vis) * 100.0, 1)

    return {
        "source": ROAD_GRAPH["nodes"][req.source_id],
        "target": ROAD_GRAPH["nodes"][req.target_id],
        "hub": ROAD_GRAPH["nodes"][tridir_res["hub_id"]],
        "dijkstra": dijkstra_res,
        "tridirectional": tridir_res,
        "comparison": {
            "dijkstra_visited": dijkstra_res["visited_count"],
            "tridirectional_visited": tridir_res["visited_count"],
            "node_reduction_pct": node_reduction_pct,
            "dijkstra_time_ms": dijkstra_res["execution_time_ms"],
            "tridirectional_time_ms": tridir_res["execution_time_ms"],
            "dijkstra_distance_miles": dijkstra_res["final_distance_miles"],
            "tridirectional_distance_miles": tridir_res["final_distance_miles"],
        },
    }


@app.websocket("/ws/race")
async def websocket_race(websocket: WebSocket) -> None:
    """Streams synchronized step-by-step frames for Dijkstra and Tri-Directional Search over WebSocket."""
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        source_id = int(payload.get("source_id", 24))
        target_id = int(payload.get("target_id", 214))
        hub_id = payload.get("hub_id", "auto")
        delay_ms = float(payload.get("delay_ms", 16.0))

        dijkstra_res = run_dijkstra(ROAD_GRAPH, source_id, target_id)
        tridir_res = run_tridirectional_search(
            ROAD_GRAPH, source_id, target_id, hub_id
        )

        max_steps = max(len(dijkstra_res["steps"]), len(tridir_res["steps"]))
        await websocket.send_json(
            {
                "type": "init",
                "total_frames": max_steps,
                "hub_id": tridir_res["hub_id"],
                "hub_label": tridir_res["hub_label"],
            }
        )

        for idx in range(max_steps):
            d_step = (
                dijkstra_res["steps"][idx]
                if idx < len(dijkstra_res["steps"])
                else None
            )
            t_step = (
                tridir_res["steps"][idx]
                if idx < len(tridir_res["steps"])
                else None
            )
            await websocket.send_json(
                {
                    "type": "frame",
                    "frame_index": idx,
                    "dijkstra_step": d_step,
                    "tridirectional_step": t_step,
                }
            )
            if delay_ms > 0:
                await asyncio.sleep(min(delay_ms, 200.0) / 1000.0)

        await websocket.send_json(
            {
                "type": "complete",
                "dijkstra": {
                    "visited_count": dijkstra_res["visited_count"],
                    "execution_time_ms": dijkstra_res["execution_time_ms"],
                    "final_distance_miles": dijkstra_res["final_distance_miles"],
                    "path_nodes": dijkstra_res["path_nodes"],
                    "path_edges": dijkstra_res["path_edges"],
                },
                "tridirectional": {
                    "visited_count": tridir_res["visited_count"],
                    "execution_time_ms": tridir_res["execution_time_ms"],
                    "final_distance_miles": tridir_res["final_distance_miles"],
                    "path_nodes": tridir_res["path_nodes"],
                    "path_edges": tridir_res["path_edges"],
                },
            }
        )
    except WebSocketDisconnect:
        pass


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serves the main interactive SVG visualizer application."""
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
