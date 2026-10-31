"""Automated verification suite for the 336-city US road network and pathfinding algorithms."""

from __future__ import annotations
import unittest
from app.algorithms import run_dijkstra, run_tridirectional_search
from app.graph_builder import build_us_road_network


class TestUSRoadPathfinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = build_us_road_network(k_neighbors=4)

    def test_336_cities_across_50_states(self) -> None:
        stats = self.graph["stats"]
        self.assertEqual(stats["node_count"], 336)
        self.assertEqual(stats["states_covered"], 50)
        self.assertGreaterEqual(stats["avg_degree"], 3.0)
        self.assertLessEqual(stats["avg_degree"], 5.0)

    def test_albers_svg_bounds(self) -> None:
        for city in self.graph["nodes"]:
            self.assertGreaterEqual(city["svg_x"], 0.0)
            self.assertLessEqual(city["svg_x"], 1200.0)
            self.assertGreaterEqual(city["svg_y"], 0.0)
            self.assertLessEqual(city["svg_y"], 750.0)

    def test_dijkstra_and_tridirectional_reachability(self) -> None:
        # Los Angeles, CA (24) -> New York, NY (211)
        id_by_label = {c["label"]: c["id"] for c in self.graph["nodes"]}
        la_id = id_by_label["Los Angeles, CA"]
        ny_id = id_by_label["New York, NY"]

        d_res = run_dijkstra(self.graph, la_id, ny_id)
        t_res = run_tridirectional_search(self.graph, la_id, ny_id, "auto")

        self.assertGreater(len(d_res["path_nodes"]), 3)
        self.assertEqual(d_res["path_nodes"][0], la_id)
        self.assertEqual(d_res["path_nodes"][-1], ny_id)

        self.assertGreater(len(t_res["path_nodes"]), 3)
        self.assertEqual(t_res["path_nodes"][0], la_id)
        self.assertEqual(t_res["path_nodes"][-1], ny_id)
        self.assertLess(t_res["visited_count"], d_res["visited_count"])


if __name__ == "__main__":
    unittest.main()
