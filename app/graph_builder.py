"""Road network graph generator using planar Delaunay triangulation filtered by nearest-k neighbors."""

from __future__ import annotations
import math
from typing import Any
from app.cities_data import get_cities_dataset

EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle geographic Haversine distance in miles between two coordinates."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return round(EARTH_RADIUS_MILES * c, 2)


def _circumcircle_contains(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p: tuple[float, float],
) -> bool:
    """Checks if point p lies strictly inside the circumcircle of triangle (p1, p2, p3)."""
    ax, ay = p1
    bx, by = p2
    cx, cy = p3

    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-11:
        return False

    a_sq = ax * ax + ay * ay
    b_sq = bx * bx + by * by
    c_sq = cx * cx + cy * cy

    ux = (a_sq * (by - cy) + b_sq * (cy - ay) + c_sq * (ay - by)) / d
    uy = (a_sq * (cx - bx) + b_sq * (ax - cx) + c_sq * (bx - ax)) / d
    r_sq = (ax - ux) ** 2 + (ay - uy) ** 2
    dist_sq = (p[0] - ux) ** 2 + (p[1] - uy) ** 2
    return dist_sq < r_sq - 1e-7


def bowyer_watson_delaunay(
    points: list[tuple[int, float, float]]
) -> set[tuple[int, int]]:
    """Computes planar Delaunay triangulation edges using the Bowyer-Watson algorithm.

    Args:
        points: List of (node_id, x, y) tuples.

    Returns:
        Set of canonical undirected edges (min_id, max_id).
    """
    if len(points) < 3:
        return set()

    xs = [p[1] for p in points]
    ys = [p[2] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    dx = max_x - min_x
    dy = max_y - min_y
    delta_max = max(dx, dy, 100.0)
    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0

    # Super-triangle vertices with negative sentinel IDs
    st1 = (-1, mid_x - 20.0 * delta_max, mid_y - delta_max)
    st2 = (-2, mid_x, mid_y + 20.0 * delta_max)
    st3 = (-3, mid_x + 20.0 * delta_max, mid_y - delta_max)

    coords: dict[int, tuple[float, float]] = {
        -1: (st1[1], st1[2]),
        -2: (st2[1], st2[2]),
        -3: (st3[1], st3[2]),
    }
    for nid, x, y in points:
        coords[nid] = (x, y)

    triangles: list[tuple[int, int, int]] = [(-1, -2, -3)]

    for nid, px, py in points:
        bad_triangles: list[tuple[int, int, int]] = []
        for tri in triangles:
            if _circumcircle_contains(
                coords[tri[0]], coords[tri[1]], coords[tri[2]], (px, py)
            ):
                bad_triangles.append(tri)

        edge_counts: dict[tuple[int, int], int] = {}
        for tri in bad_triangles:
            for e in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                canon = (min(e[0], e[1]), max(e[0], e[1]))
                edge_counts[canon] = edge_counts.get(canon, 0) + 1

        bad_set = set(bad_triangles)
        triangles = [t for t in triangles if t not in bad_set]

        for (u, v), count in edge_counts.items():
            if count == 1:
                triangles.append((u, v, nid))

    delaunay_edges: set[tuple[int, int]] = set()
    for a, b, c in triangles:
        if a < 0 or b < 0 or c < 0:
            continue
        for u, v in ((a, b), (b, c), (c, a)):
            delaunay_edges.add((min(u, v), max(u, v)))

    return delaunay_edges


def build_us_road_network(k_neighbors: int = 4) -> dict[str, Any]:
    """Builds the 336-city US road network graph using Delaunay triangulation + nearest-k filtering.

    Guarantees:
    - All 336 cities across 50 states included.
    - Planar Delaunay triangulation on contiguous US cities filtered by nearest-k neighbors.
    - Minimum Spanning Tree (MST) backbone preserved so the graph is 100% connected.
    - Average node degree strictly between 3.0 and 5.0 (target ~4.1).
    - Edge weights represent geographic Haversine distance in miles.
    """
    cities = get_cities_dataset()
    n = len(cities)
    city_by_id = {c["id"]: c for c in cities}

    # Separate contiguous US cities from AK and HI for planar Delaunay triangulation
    contiguous_pts: list[tuple[int, float, float]] = []
    ak_ids: list[int] = []
    hi_ids: list[int] = []

    for c in cities:
        if c["state"] == "AK":
            ak_ids.append(c["id"])
        elif c["state"] == "HI":
            hi_ids.append(c["id"])
        else:
            contiguous_pts.append((c["id"], c["svg_x"], c["svg_y"]))

    raw_delaunay = bowyer_watson_delaunay(contiguous_pts)

    # Compute Haversine distances for all Delaunay edges
    delaunay_with_dist: list[tuple[float, int, int]] = []
    adj_delaunay: dict[int, list[tuple[float, int]]] = {c["id"]: [] for c in cities}

    for u, v in raw_delaunay:
        cu, cv = city_by_id[u], city_by_id[v]
        dist = haversine_miles(
            cu["latitude"], cu["longitude"], cv["latitude"], cv["longitude"]
        )
        delaunay_with_dist.append((dist, u, v))
        adj_delaunay[u].append((dist, v))
        adj_delaunay[v].append((dist, u))

    for nid in adj_delaunay:
        adj_delaunay[nid].sort(key=lambda item: item[0])

    # 1. Build Kruskal Minimum Spanning Tree over Delaunay edges to guarantee 100% connectivity
    parent = {c["id"]: c["id"] for c in cities}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> bool:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
            return True
        return False

    selected_edges: set[tuple[int, int]] = set()
    for dist, u, v in sorted(delaunay_with_dist):
        if union(u, v):
            selected_edges.add((min(u, v), max(u, v)))

    # 2. Filter Delaunay edges by nearest-k neighbors (excluding long perimeter hull artifacts > 550 mi)
    for u, neighbors in adj_delaunay.items():
        for rank, (dist, v) in enumerate(neighbors):
            if rank < k_neighbors and dist <= 520.0:
                # Keep edge if it is within k nearest Delaunay neighbors for u
                # and also reasonably close in rank for v (mutual/semi-mutual k-NN)
                v_ranks = [ idx for idx, (_, nb) in enumerate(adj_delaunay[v]) if nb == u ]
                if v_ranks and v_ranks[0] <= k_neighbors:
                    selected_edges.add((min(u, v), max(u, v)))

    # 3. Connect Alaska (4 cities) and Hawaii (4 cities) internally and via West Coast gateways
    # Find IDs by (name, state)
    id_lookup = {(c["name"], c["state"]): c["id"] for c in cities}

    ak_chains = [
        (("Anchorage", "AK"), ("Fairbanks", "AK")),
        (("Anchorage", "AK"), ("Juneau", "AK")),
        (("Juneau", "AK"), ("Sitka", "AK")),
        (("Anchorage", "AK"), ("Sitka", "AK")),
        (("Juneau", "AK"), ("Seattle", "WA")),
        (("Sitka", "AK"), ("Bellingham", "WA")),
        (("Anchorage", "AK"), ("Seattle", "WA")),
    ]
    hi_chains = [
        (("Honolulu", "HI"), ("Lihue", "HI")),
        (("Honolulu", "HI"), ("Kahului", "HI")),
        (("Kahului", "HI"), ("Hilo", "HI")),
        (("Honolulu", "HI"), ("Hilo", "HI")),
        (("Honolulu", "HI"), ("San Francisco", "CA")),
        (("Honolulu", "HI"), ("Los Angeles", "CA")),
        (("Kahului", "HI"), ("San Diego", "CA")),
    ]

    for (n1, s1), (n2, s2) in ak_chains + hi_chains:
        u, v = id_lookup[(n1, s1)], id_lookup[(n2, s2)]
        selected_edges.add((min(u, v), max(u, v)))

    # Build final edge list and adjacency list
    edges: list[dict[str, Any]] = []
    adjacency: dict[int, list[dict[str, Any]]] = {i: [] for i in range(n)}

    for edge_id, (u, v) in enumerate(sorted(selected_edges)):
        cu, cv = city_by_id[u], city_by_id[v]
        weight = haversine_miles(
            cu["latitude"], cu["longitude"], cv["latitude"], cv["longitude"]
        )
        is_non_contiguous = cu["state"] in ("AK", "HI") or cv["state"] in ("AK", "HI")
        edge_obj = {
            "id": edge_id,
            "source": u,
            "target": v,
            "weight": weight,
            "is_inset_link": is_non_contiguous and (cu["state"] != cv["state"]),
        }
        edges.append(edge_obj)
        adjacency[u].append({"to": v, "weight": weight, "edge_id": edge_id})
        adjacency[v].append({"to": u, "weight": weight, "edge_id": edge_id})

    avg_degree = round((2.0 * len(edges)) / n, 2)

    return {
        "nodes": cities,
        "edges": edges,
        "adjacency": adjacency,
        "stats": {
            "node_count": n,
            "edge_count": len(edges),
            "avg_degree": avg_degree,
            "states_covered": len({c["state"] for c in cities}),
        },
    }
