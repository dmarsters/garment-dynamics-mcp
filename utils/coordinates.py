"""
Coordinate utilities for garment-dynamics.
Distance, interpolation, nearest-neighbor in 7D parameter space.
"""

import math


PARAMETER_NAMES = [
    "silhouette_volume",
    "structural_rigidity",
    "construction_complexity",
    "surface_activity",
    "hem_geometry",
    "exposure_ratio",
    "temporal_register",
]


def euclidean_distance(coords_a: dict, coords_b: dict) -> float:
    """Euclidean distance between two 7D coordinate dicts."""
    total = 0.0
    for p in PARAMETER_NAMES:
        diff = coords_a.get(p, 0.0) - coords_b.get(p, 0.0)
        total += diff * diff
    return math.sqrt(total)


def interpolate(coords_a: dict, coords_b: dict, steps: int = 10) -> list:
    """Linear interpolation between two coordinate dicts."""
    result = []
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 0
        point = {}
        for p in PARAMETER_NAMES:
            va = coords_a.get(p, 0.0)
            vb = coords_b.get(p, 0.0)
            point[p] = round(va + t * (vb - va), 4)
        result.append(point)
    return result


def find_nearest(target_coords: dict, catalog: dict, max_results: int = 5, exclude: str = "") -> list:
    """Find nearest garments to target coordinates in 7D space."""
    distances = []
    for name, garment in catalog.items():
        if name == exclude:
            continue
        coords = garment.get("coordinates", garment)
        d = euclidean_distance(target_coords, coords)
        distances.append((name, d))
    distances.sort(key=lambda x: x[1])
    return distances[:max_results]


def apply_modifier(coordinates: dict, modifier: str) -> dict:
    """Apply a modifier to garment coordinates.
    
    Modifiers:
    - oversized: push volume up, rigidity down
    - cropped: reduce hem_geometry, increase exposure
    - fitted: reduce volume, increase rigidity
    - elongated: increase hem_geometry, reduce exposure
    - distressed: increase surface_activity, push temporal forward
    """
    result = dict(coordinates)
    
    modifiers = {
        "oversized": {
            "silhouette_volume": 0.20,
            "structural_rigidity": -0.15,
            "exposure_ratio": -0.10,
        },
        "cropped": {
            "hem_geometry": -0.15,
            "exposure_ratio": 0.15,
            "silhouette_volume": -0.10,
        },
        "fitted": {
            "silhouette_volume": -0.15,
            "structural_rigidity": 0.10,
            "exposure_ratio": 0.05,
        },
        "elongated": {
            "hem_geometry": 0.15,
            "exposure_ratio": -0.10,
            "silhouette_volume": 0.05,
        },
        "distressed": {
            "surface_activity": 0.20,
            "temporal_register": 0.10,
            "construction_complexity": 0.10,
        },
    }
    
    shifts = modifiers.get(modifier, {})
    for param, delta in shifts.items():
        if param in result:
            result[param] = max(0.0, min(1.0, round(result[param] + delta, 4)))
    
    return result
