"""Pathfinding algorithms: Standard Single-Source Dijkstra vs. 3-Directional A* (3-Way Heuristic) Search."""

from __future__ import annotations
import heapq
import math
import time
from typing import Any
from app.graph_builder import haversine_miles


def _reconstruct_single_path(
    parent: dict[int, int | None],
    parent_edge: dict[int, int | None],
    start: int,
    end: int,
) -> tuple[list[int], list[int]]:
    """Reconstructs node list and edge list from start to end using parent maps."""
    nodes: list[int] = []
    edges: list[int] = []
    curr: int | None = end
    while curr is not None:
        nodes.append(curr)
        edge_id = parent_edge.get(curr)
        if edge_id is not None:
            edges.append(edge_id)
        if curr == start:
            break
        curr = parent.get(curr)
    nodes.reverse()
    edges.reverse()
    return nodes, edges


def select_dynamic_hub(
    graph: dict[str, Any], source_id: int, target_id: int
) -> int:
    """Selects an optimal intermediate Hub city M between Source S and Target T.

    Uses a shortest-path geodesic landmark heuristic so that M lies directly along
    or near the natural corridor between S and T, maximizing 3-directional A* convergence.
    """
    nodes = graph["nodes"]
    city_by_id = {c["id"]: c for c in nodes}
    s_city = city_by_id[source_id]
    t_city = city_by_id[target_id]

    mid_lat = (s_city["latitude"] + t_city["latitude"]) / 2.0
    mid_lon = (s_city["longitude"] + t_city["longitude"]) / 2.0
    direct_dist = max(
        1.0,
        haversine_miles(
            s_city["latitude"],
            s_city["longitude"],
            t_city["latitude"],
            t_city["longitude"],
        ),
    )

    best_hub = source_id
    best_score = float("inf")

    for c in nodes:
        cid = c["id"]
        if cid in (source_id, target_id):
            continue
        d_s = haversine_miles(
            s_city["latitude"], s_city["longitude"], c["latitude"], c["longitude"]
        )
        d_t = haversine_miles(
            c["latitude"], c["longitude"], t_city["latitude"], t_city["longitude"]
        )
        d_mid = haversine_miles(mid_lat, mid_lon, c["latitude"], c["longitude"])

        detour_penalty = (d_s + d_t) - direct_dist
        balance_penalty = abs(d_s - d_t) * 0.65
        score = detour_penalty * 2.2 + balance_penalty + d_mid * 0.25
        if score < best_score:
            best_score = score
            best_hub = cid

    return best_hub


def run_dijkstra(
    graph: dict[str, Any], source_id: int, target_id: int
) -> dict[str, Any]:
    """Executes Standard Single-Source Dijkstra's Algorithm with full step-by-step telemetry."""
    adj = graph["adjacency"]
    city_by_id = {c["id"]: c for c in graph["nodes"]}

    algo_elapsed_ns = 0

    dist: dict[int, float] = {source_id: 0.0}
    parent: dict[int, int | None] = {source_id: None}
    parent_edge: dict[int, int | None] = {source_id: None}
    visited: set[int] = set()
    visited_edges: list[int] = []

    pq: list[tuple[float, int]] = [(0.0, source_id)]
    heap_pushes = 1
    heap_pops = 0

    steps: list[dict[str, Any]] = []

    while pq:
        step_t0 = time.perf_counter_ns()
        d_u, u = heapq.heappop(pq)
        heap_pops += 1

        if u in visited:
            algo_elapsed_ns += time.perf_counter_ns() - step_t0
            continue

        visited.add(u)
        in_edge = parent_edge.get(u)
        if in_edge is not None:
            visited_edges.append(in_edge)

        relaxations: list[dict[str, Any]] = []
        active_edges: list[int] = []

        if u == target_id:
            algo_elapsed_ns += time.perf_counter_ns() - step_t0
            pq_preview = [
                {
                    "node_id": nid,
                    "label": city_by_id[nid]["label"],
                    "dist": round(d, 1),
                }
                for d, nid in heapq.nsmallest(6, pq)
                if nid not in visited
            ][:4]
            steps.append(
                {
                    "step": len(steps) + 1,
                    "current_node": u,
                    "current_label": city_by_id[u]["label"],
                    "current_dist": round(d_u, 2),
                    "tree_edge": in_edge,
                    "active_edges": [],
                    "visited_count": len(visited),
                    "pq_size": len(pq),
                    "heap_pushes": heap_pushes,
                    "heap_pops": heap_pops,
                    "pq_preview": pq_preview,
                    "relaxations": [
                        {
                            "from": city_by_id[u]["label"],
                            "to": city_by_id[u]["label"],
                            "old_dist": round(d_u, 1),
                            "new_dist": round(d_u, 1),
                            "note": "TARGET REACHED",
                        }
                    ],
                }
            )
            break

        raw_relaxations: list[tuple[int, float, float]] = []
        for neighbor in adj[u]:
            v = neighbor["to"]
            weight = neighbor["weight"]
            edge_id = neighbor["edge_id"]
            if v in visited:
                continue

            new_dist = round(d_u + weight, 2)
            old_dist = dist.get(v, float("inf"))
            if new_dist < old_dist:
                dist[v] = new_dist
                parent[v] = u
                parent_edge[v] = edge_id
                heapq.heappush(pq, (new_dist, v))
                heap_pushes += 1
                active_edges.append(edge_id)
                raw_relaxations.append((v, old_dist, new_dist))

        algo_elapsed_ns += time.perf_counter_ns() - step_t0

        for v, old_dist, new_dist in raw_relaxations[:5]:
            relaxations.append(
                {
                    "from": city_by_id[u]["label"],
                    "to": city_by_id[v]["label"],
                    "old_dist": "∞" if math.isinf(old_dist) else round(old_dist, 1),
                    "new_dist": round(new_dist, 1),
                }
            )

        pq_preview = [
            {
                "node_id": nid,
                "label": city_by_id[nid]["label"],
                "dist": round(d, 1),
            }
            for d, nid in heapq.nsmallest(6, pq)
            if nid not in visited
        ][:4]

        steps.append(
            {
                "step": len(steps) + 1,
                "current_node": u,
                "current_label": city_by_id[u]["label"],
                "current_dist": round(d_u, 2),
                "tree_edge": in_edge,
                "active_edges": active_edges,
                "visited_count": len(visited),
                "pq_size": len(pq),
                "heap_pushes": heap_pushes,
                "heap_pops": heap_pops,
                "pq_preview": pq_preview,
                "relaxations": relaxations[:5],
            }
        )

    exec_time_ms = round(algo_elapsed_ns / 1_000_000.0, 3)

    path_nodes, path_edges = _reconstruct_single_path(
        parent, parent_edge, source_id, target_id
    )
    final_distance = round(dist.get(target_id, float("inf")), 2)

    return {
        "algorithm": "Standard Single-Source Dijkstra",
        "source_id": source_id,
        "target_id": target_id,
        "visited_count": len(visited),
        "visited_nodes": list(visited),
        "visited_edges": visited_edges,
        "execution_time_ms": exec_time_ms,
        "final_distance_miles": final_distance,
        "path_nodes": path_nodes,
        "path_edges": path_edges,
        "heap_pushes": heap_pushes,
        "heap_pops": heap_pops,
        "steps": steps,
    }


def run_tridirectional_search(
    graph: dict[str, Any],
    source_id: int,
    target_id: int,
    hub_id: int | str | None = "auto",
) -> dict[str, Any]:
    """Executes 3-Directional A* Search with 3 heuristic-guided search frontiers: S, M, and T.

    Maintains 3 concurrent A* priority queues ordered by f(n) = g(n) + h(n):
      - Frontier 'S' (Origin S, Neon Blue):
          g_S(n) = road distance from S; h_S(n) = Haversine distance to M (or T).
      - Frontier 'T' (Destination T, Neon Green):
          g_T(n) = road distance from T; h_T(n) = Haversine distance to M (or S).
      - Frontier 'M' (Intermediate Hub M, Neon Purple):
          g_M(n) = road distance from M; h_M(n) = directional Haversine heuristic toward
          whichever leg (S <-> M or M <-> T) is still unconverged.
    """
    adj = graph["adjacency"]
    city_by_id = {c["id"]: c for c in graph["nodes"]}

    resolved_hub_id: int
    if hub_id is None or hub_id == "auto" or hub_id == "":
        resolved_hub_id = select_dynamic_hub(graph, source_id, target_id)
        hub_mode = "auto"
    else:
        resolved_hub_id = int(hub_id)
        hub_mode = "manual"

    s_city = city_by_id[source_id]
    m_city = city_by_id[resolved_hub_id]
    t_city = city_by_id[target_id]

    # Precompute Haversine heuristics h(v -> S), h(v -> M), h(v -> T) for all 336 cities
    h_to_s: dict[int, float] = {}
    h_to_m: dict[int, float] = {}
    h_to_t: dict[int, float] = {}
    for cid, c in city_by_id.items():
        lat, lon = c["latitude"], c["longitude"]
        h_to_s[cid] = haversine_miles(lat, lon, s_city["latitude"], s_city["longitude"])
        h_to_m[cid] = haversine_miles(lat, lon, m_city["latitude"], m_city["longitude"])
        h_to_t[cid] = haversine_miles(lat, lon, t_city["latitude"], t_city["longitude"])

    def heuristic(frontier: str, nid: int, sm_locked: bool, mt_locked: bool) -> float:
        """Admissible/directional A* heuristic h(n) in miles for each of the 3 frontiers."""
        if frontier == "S":
            return h_to_m[nid]
        if frontier == "T":
            return h_to_m[nid]
        # Frontier M expands bidirectionally toward S and T; once one leg locks, steer strictly toward the remaining leg
        if not sm_locked and not mt_locked:
            return min(h_to_s[nid], h_to_t[nid])
        if not sm_locked:
            return h_to_s[nid]
        return h_to_t[nid]

    algo_elapsed_ns = 0

    # g-scores (actual road distance from each frontier's origin)
    dist: dict[str, dict[int, float]] = {
        "S": {source_id: 0.0},
        "M": {resolved_hub_id: 0.0},
        "T": {target_id: 0.0},
    }
    parent: dict[str, dict[int, int | None]] = {
        "S": {source_id: None},
        "M": {resolved_hub_id: None},
        "T": {target_id: None},
    }
    parent_edge: dict[str, dict[int, int | None]] = {
        "S": {source_id: None},
        "M": {resolved_hub_id: None},
        "T": {target_id: None},
    }
    visited: dict[str, set[int]] = {
        "S": set(),
        "M": set(),
        "T": set(),
    }

    # Priority queue tuples: (f_score, g_score, h_score, node_id)
    init_hs = round(heuristic("S", source_id, False, False), 2)
    init_hm = round(heuristic("M", resolved_hub_id, False, False), 2)
    init_ht = round(heuristic("T", target_id, False, False), 2)

    pqs: dict[str, list[tuple[float, float, float, int]]] = {
        "S": [(init_hs, 0.0, init_hs, source_id)],
        "M": [(init_hm, 0.0, init_hm, resolved_hub_id)],
        "T": [(init_ht, 0.0, init_ht, target_id)],
    }

    heap_pushes = 3
    heap_pops = 0

    best_sm = float("inf")
    meet_sm: int | None = None

    best_mt = float("inf")
    meet_mt: int | None = None

    if resolved_hub_id == source_id:
        best_sm = 0.0
        meet_sm = source_id
    if resolved_hub_id == target_id:
        best_mt = 0.0
        meet_mt = target_id

    steps: list[dict[str, Any]] = []
    frontier_order = ["S", "M", "T"]
    turn_idx = 0

    def _clean_top(f_key: str) -> float:
        q = pqs[f_key]
        while q and q[0][3] in visited[f_key]:
            heapq.heappop(q)
        return q[0][0] if q else float("inf")

    while True:
        step_t0 = time.perf_counter_ns()
        top_s = _clean_top("S")
        top_m = _clean_top("M")
        top_t = _clean_top("T")

        sm_done = meet_sm is not None
        mt_done = meet_mt is not None

        if sm_done and mt_done:
            algo_elapsed_ns += time.perf_counter_ns() - step_t0
            break

        active_frontiers: list[str] = []
        if not sm_done and top_s < float("inf"):
            active_frontiers.append("S")
        if (not sm_done or not mt_done) and top_m < float("inf"):
            active_frontiers.append("M")
        if not mt_done and top_t < float("inf"):
            active_frontiers.append("T")

        if not active_frontiers:
            algo_elapsed_ns += time.perf_counter_ns() - step_t0
            break

        chosen_f = None
        for offset in range(3):
            candidate = frontier_order[(turn_idx + offset) % 3]
            if candidate in active_frontiers:
                chosen_f = candidate
                turn_idx = (turn_idx + offset + 1) % 3
                break

        if chosen_f is None:
            algo_elapsed_ns += time.perf_counter_ns() - step_t0
            break

        f_u, g_u, h_u, u = heapq.heappop(pqs[chosen_f])
        heap_pops += 1
        if u in visited[chosen_f]:
            algo_elapsed_ns += time.perf_counter_ns() - step_t0
            continue

        visited[chosen_f].add(u)
        in_edge = parent_edge[chosen_f].get(u)

        if u in dist["S"] and u in dist["M"]:
            cand_sm = dist["S"][u] + dist["M"][u]
            if cand_sm < best_sm:
                best_sm = cand_sm
                meet_sm = u
                sm_done = True

        if u in dist["M"] and u in dist["T"]:
            cand_mt = dist["M"][u] + dist["T"][u]
            if cand_mt < best_mt:
                best_mt = cand_mt
                meet_mt = u
                mt_done = True

        # Raw relaxations tuple: (v, old_g, new_g, h_v, f_v)
        raw_relaxations: list[tuple[int, float, float, float, float]] = []
        active_edges: list[int] = []

        for neighbor in adj[u]:
            v = neighbor["to"]
            weight = neighbor["weight"]
            edge_id = neighbor["edge_id"]

            if v in visited[chosen_f]:
                continue

            new_g = round(g_u + weight, 2)
            old_g = dist[chosen_f].get(v, float("inf"))
            if new_g < old_g:
                dist[chosen_f][v] = new_g
                parent[chosen_f][v] = u
                parent_edge[chosen_f][v] = edge_id

                h_v = round(heuristic(chosen_f, v, sm_done, mt_done), 2)
                f_v = round(new_g + h_v, 2)
                heapq.heappush(pqs[chosen_f], (f_v, new_g, h_v, v))
                heap_pushes += 1
                active_edges.append(edge_id)
                raw_relaxations.append((v, old_g, new_g, h_v, f_v))

                if chosen_f in ("S", "M") and v in dist["S"] and v in dist["M"]:
                    cand_sm = dist["S"][v] + dist["M"][v]
                    if cand_sm < best_sm:
                        best_sm = cand_sm
                        meet_sm = v
                        sm_done = True

                if chosen_f in ("M", "T") and v in dist["M"] and v in dist["T"]:
                    cand_mt = dist["M"][v] + dist["T"][v]
                    if cand_mt < best_mt:
                        best_mt = cand_mt
                        meet_mt = v
                        mt_done = True

        algo_elapsed_ns += time.perf_counter_ns() - step_t0

        relaxations: list[dict[str, Any]] = [
            {
                "frontier": chosen_f,
                "from": city_by_id[u]["label"],
                "to": city_by_id[v]["label"],
                "old_dist": "∞" if math.isinf(old_g) else round(old_g, 1),
                "new_dist": round(new_g, 1),
                "h_val": round(h_v, 1),
                "f_val": round(f_v, 1),
            }
            for v, old_g, new_g, h_v, f_v in raw_relaxations[:5]
        ]

        unique_visited = visited["S"] | visited["M"] | visited["T"]
        total_pq_size = len(pqs["S"]) + len(pqs["M"]) + len(pqs["T"])

        pq_preview: list[dict[str, Any]] = []
        for f_name in ("S", "M", "T"):
            for f_val, g_val, h_val, nid in heapq.nsmallest(4, pqs[f_name]):
                if nid not in visited[f_name]:
                    pq_preview.append(
                        {
                            "frontier": f_name,
                            "node_id": nid,
                            "label": city_by_id[nid]["label"],
                            "dist": round(f_val, 1),
                            "g": round(g_val, 1),
                            "h": round(h_val, 1),
                        }
                    )
                    break

        steps.append(
            {
                "step": len(steps) + 1,
                "frontier": chosen_f,
                "current_node": u,
                "current_label": city_by_id[u]["label"],
                "current_dist": round(g_u, 2),
                "current_f": round(f_u, 2),
                "current_h": round(h_u, 2),
                "tree_edge": in_edge,
                "active_edges": active_edges,
                "visited_count": len(unique_visited),
                "frontier_counts": {
                    "S": len(visited["S"]),
                    "M": len(visited["M"]),
                    "T": len(visited["T"]),
                },
                "pq_size": total_pq_size,
                "pq_sizes": {
                    "S": len(pqs["S"]),
                    "M": len(pqs["M"]),
                    "T": len(pqs["T"]),
                },
                "heap_pushes": heap_pushes,
                "heap_pops": heap_pops,
                "pq_preview": pq_preview,
                "relaxations": relaxations[:5],
                "collision_state": {
                    "sm_locked": sm_done,
                    "mt_locked": mt_done,
                    "best_sm": None if math.isinf(best_sm) else round(best_sm, 1),
                    "best_mt": None if math.isinf(best_mt) else round(best_mt, 1),
                },
            }
        )

    exec_time_ms = round(algo_elapsed_ns / 1_000_000.0, 3)

    path_nodes: list[int] = []
    path_edges: list[int] = []

    if meet_sm is not None and meet_mt is not None:
        s_to_meet_nodes, s_to_meet_edges = _reconstruct_single_path(
            parent["S"], parent_edge["S"], source_id, meet_sm
        )
        m_to_meet_nodes, m_to_meet_edges = _reconstruct_single_path(
            parent["M"], parent_edge["M"], resolved_hub_id, meet_sm
        )
        leg1_nodes = s_to_meet_nodes + list(reversed(m_to_meet_nodes[:-1]))
        leg1_edges = s_to_meet_edges + list(reversed(m_to_meet_edges))

        m_to_meet2_nodes, m_to_meet2_edges = _reconstruct_single_path(
            parent["M"], parent_edge["M"], resolved_hub_id, meet_mt
        )
        t_to_meet2_nodes, t_to_meet2_edges = _reconstruct_single_path(
            parent["T"], parent_edge["T"], target_id, meet_mt
        )
        leg2_nodes = m_to_meet2_nodes + list(reversed(t_to_meet2_nodes[:-1]))
        leg2_edges = m_to_meet2_edges + list(reversed(t_to_meet2_edges))

        path_nodes = leg1_nodes + leg2_nodes[1:]
        path_edges = leg1_edges + leg2_edges
        final_distance = round(best_sm + best_mt, 2)
    else:
        final_distance = float("inf")

    unique_visited = visited["S"] | visited["M"] | visited["T"]

    return {
        "algorithm": "3-Directional A* Search (f = g + h)",
        "source_id": source_id,
        "target_id": target_id,
        "hub_id": resolved_hub_id,
        "hub_label": city_by_id[resolved_hub_id]["label"],
        "hub_mode": hub_mode,
        "meet_sm_id": meet_sm,
        "meet_sm_label": city_by_id[meet_sm]["label"] if meet_sm is not None else None,
        "meet_mt_id": meet_mt,
        "meet_mt_label": city_by_id[meet_mt]["label"] if meet_mt is not None else None,
        "visited_count": len(unique_visited),
        "frontier_visited_counts": {
            "S": len(visited["S"]),
            "M": len(visited["M"]),
            "T": len(visited["T"]),
        },
        "execution_time_ms": exec_time_ms,
        "final_distance_miles": final_distance,
        "path_nodes": path_nodes,
        "path_edges": path_edges,
        "heap_pushes": heap_pushes,
        "heap_pops": heap_pops,
        "steps": steps,
    }
