"""
Layer 2: Deterministic computation (0 tokens).
Fabric interaction, form behavior, color, distance, trajectory, intent.
"""

from layers.taxonomy import (
    get_garment_catalog, get_fabric_catalog, get_color_catalog,
    get_form_catalog, get_keyword_index_data,
)
from utils.coordinates import euclidean_distance, interpolate, find_nearest
from utils.fabric_physics import (
    compute_fabric_coordinate_shift, apply_fabric_shifts,
    compute_drape_behavior, compute_light_on_fabric, compute_form_behavior,
)
from utils.keyword_index import tokenize_intent, search_by_keywords


def register_computation_tools(mcp):
    """Register all Layer 2 tools on the MCP server."""
    
    @mcp.tool()
    def compute_garment_on_form(
        garment_name: str,
        fabric_name: str = "",
        form: str = "standing_mannequin",
        environment: str = "still",
    ) -> dict:
        """Compute garment behavior on a non-human form or in isolation.
        
        Layer 2: Deterministic computation (0 tokens).
        
        The key independence tool — garment geometry WITHOUT a pose.
        
        Args:
            garment_name: Any canonical garment name
            fabric_name: Override default fabric (empty = use generic defaults)
            form: "standing_mannequin", "dress_form", "hanger", "flat_lay",
                  "draped_on_chair", "pooled_on_floor", "wind_blown",
                  "on_body_walking", "on_body_seated"
            environment: "still", "light_breeze", "strong_wind", 
                         "underwater", "zero_gravity"
        
        Returns silhouette, drape_map, fold_geometry, hem_state,
        light_surfaces, compositional_weight.
        """
        garments = get_garment_catalog()
        fabrics = get_fabric_catalog()
        forms = get_form_catalog()
        
        garment = garments.get(garment_name)
        if not garment:
            return {"error": f"Garment '{garment_name}' not found"}
        
        form_data = forms.get(form)
        if not form_data:
            return {"error": f"Form '{form}' not found", "available": sorted(forms.keys())}
        
        # Use specified fabric or create generic defaults
        if fabric_name:
            fabric = fabrics.get(fabric_name)
            if not fabric:
                return {"error": f"Fabric '{fabric_name}' not found"}
        else:
            # Generic mid-range fabric
            fabric = {
                "weight": 0.35, "drape_coefficient": 0.50,
                "recovery": 0.40, "surface": "moderate-texture",
                "light_interaction": "diffuse-moderate",
                "fold_character": "medium-soft-folds",
            }
        
        # Compute form behavior
        form_result = compute_form_behavior(garment, fabric, form_data, environment)
        
        # Compute drape
        drape = compute_drape_behavior(garment, fabric)
        
        # Compute fabric-modified coordinates
        shifts = compute_fabric_coordinate_shift(garment["coordinates"], fabric)
        modified_coords = apply_fabric_shifts(garment["coordinates"], shifts)
        
        return {
            "garment": garment_name,
            "form": form,
            "fabric": fabric_name or "generic",
            "environment": environment,
            "modified_coordinates": modified_coords,
            "form_behavior": form_result,
            "drape_behavior": drape,
            "silhouette_geometry": garment.get("silhouette_geometry", {}),
            "construction": garment.get("construction", {}),
        }
    
    @mcp.tool()
    def compute_garment_fabric_interaction(
        garment_name: str,
        fabric_name: str,
    ) -> dict:
        """Compute how a specific fabric transforms a garment's behavior.
        
        Layer 2: Deterministic computation (0 tokens).
        
        A ball gown in tulle vs. velvet vs. leather produces radically 
        different objects. This computes the shift.
        
        Args:
            garment_name: Any canonical garment
            fabric_name: Any fabric from the physics library
        
        Returns modified coordinates, silhouette change, drape change,
        fold change, light change, tension points.
        """
        garments = get_garment_catalog()
        fabrics = get_fabric_catalog()
        
        garment = garments.get(garment_name)
        if not garment:
            return {"error": f"Garment '{garment_name}' not found"}
        
        fabric = fabrics.get(fabric_name)
        if not fabric:
            return {"error": f"Fabric '{fabric_name}' not found"}
        
        # Coordinate shifts
        shifts = compute_fabric_coordinate_shift(garment["coordinates"], fabric)
        modified = apply_fabric_shifts(garment["coordinates"], shifts)
        
        # Drape behavior
        drape = compute_drape_behavior(garment, fabric)
        
        # Light interaction
        light = compute_light_on_fabric(fabric)
        
        # Tension analysis: where fabric fights garment structure
        garment_rigidity = garment["coordinates"]["structural_rigidity"]
        fabric_drape = fabric["drape_coefficient"]
        tension = abs(garment_rigidity - (1.0 - fabric_drape))
        
        if tension > 0.5:
            tension_desc = "high-conflict: fabric fights garment structure"
        elif tension > 0.25:
            tension_desc = "moderate: fabric partially resists garment form"
        else:
            tension_desc = "harmonious: fabric supports garment intent"
        
        return {
            "garment": garment_name,
            "fabric": fabric_name,
            "original_coordinates": garment["coordinates"],
            "coordinate_shifts": shifts,
            "modified_coordinates": modified,
            "drape_change": drape,
            "light_interaction": light,
            "structural_tension": {
                "score": round(tension, 4),
                "description": tension_desc,
                "garment_rigidity": garment_rigidity,
                "fabric_drape": fabric_drape,
            },
        }
    
    @mcp.tool()
    def compute_garment_color_interaction(
        garment_name: str,
        fabric_name: str,
        color: str,
    ) -> dict:
        """Compute how color behaves on a specific garment-fabric combination.
        
        Layer 2: Deterministic computation (0 tokens).
        
        Args:
            garment_name: Any canonical garment
            fabric_name: Any fabric from physics library
            color: Color name — "black", "white", "red", "navy", "blush",
                   "metallic_gold", "deep_emerald", "iridescent", "ivory",
                   "charcoal"
        """
        garments = get_garment_catalog()
        fabrics = get_fabric_catalog()
        colors = get_color_catalog()
        
        garment = garments.get(garment_name)
        if not garment:
            return {"error": f"Garment '{garment_name}' not found"}
        
        fabric = fabrics.get(fabric_name)
        if not fabric:
            return {"error": f"Fabric '{fabric_name}' not found"}
        
        color_data = colors.get(color)
        if not color_data:
            return {"error": f"Color '{color}' not found", "available": sorted(colors.keys())}
        
        # Light on fabric with color
        light = compute_light_on_fabric(fabric, color_data)
        
        # Volume interaction: color + garment volume
        garment_vol = garment["coordinates"]["silhouette_volume"]
        color_vol = color_data.get("volume_effect", "")
        if "expands" in color_vol:
            perceived_volume = min(1.0, garment_vol + 0.10)
        elif "contracts" in color_vol:
            perceived_volume = max(0.0, garment_vol - 0.10)
        else:
            perceived_volume = garment_vol
        
        # Mood interaction
        garment_mood = garment.get("keywords", [])
        color_mood = color_data.get("mood", [])
        shared_mood = [m for m in color_mood if m in garment_mood]
        
        return {
            "garment": garment_name,
            "fabric": fabric_name,
            "color": color,
            "color_behavior": light,
            "perceived_volume": round(perceived_volume, 4),
            "original_volume": garment_vol,
            "mood_alignment": {
                "garment_keywords": garment_mood,
                "color_mood": color_mood,
                "shared": shared_mood,
                "alignment_score": round(len(shared_mood) / max(len(color_mood), 1), 2),
            },
        }
    
    @mcp.tool()
    def compute_garment_distance(garment_a: str, garment_b: str) -> dict:
        """Euclidean distance between two garments in 7D parameter space.
        
        Layer 2: Deterministic computation (0 tokens).
        """
        catalog = get_garment_catalog()
        
        ga = catalog.get(garment_a)
        gb = catalog.get(garment_b)
        if not ga:
            return {"error": f"Garment '{garment_a}' not found"}
        if not gb:
            return {"error": f"Garment '{garment_b}' not found"}
        
        d = euclidean_distance(ga["coordinates"], gb["coordinates"])
        
        # Per-dimension deltas
        deltas = {}
        for param in ga["coordinates"]:
            deltas[param] = round(gb["coordinates"][param] - ga["coordinates"][param], 4)
        
        return {
            "garment_a": garment_a,
            "garment_b": garment_b,
            "distance": round(d, 4),
            "per_dimension_delta": deltas,
        }
    
    @mcp.tool()
    def find_nearby_garments(garment_name: str, max_results: int = 5) -> dict:
        """Find garments nearest to the given garment in 7D space.
        
        Layer 2: Deterministic distance computation (0 tokens).
        """
        catalog = get_garment_catalog()
        garment = catalog.get(garment_name)
        if not garment:
            return {"error": f"Garment '{garment_name}' not found"}
        
        nearest = find_nearest(garment["coordinates"], catalog, max_results, exclude=garment_name)
        
        return {
            "reference": garment_name,
            "nearest": [
                {"garment": name, "distance": round(d, 4)}
                for name, d in nearest
            ],
        }
    
    @mcp.tool()
    def compute_garment_trajectory(
        garment_a: str,
        garment_b: str,
        steps: int = 10,
    ) -> dict:
        """Smooth interpolation between two garments through 7D space.
        
        Layer 2: Deterministic interpolation (0 tokens).
        
        Useful for conceptual design exploration, editorial series
        showing garment evolution, finding hybrid concepts at
        intermediate coordinates.
        """
        catalog = get_garment_catalog()
        
        ga = catalog.get(garment_a)
        gb = catalog.get(garment_b)
        if not ga:
            return {"error": f"Garment '{garment_a}' not found"}
        if not gb:
            return {"error": f"Garment '{garment_b}' not found"}
        
        trajectory = interpolate(ga["coordinates"], gb["coordinates"], steps)
        
        # Find nearest known garment at each step
        waypoints = []
        for i, coords in enumerate(trajectory):
            nearest = find_nearest(coords, catalog, max_results=1)
            waypoints.append({
                "step": i,
                "t": round(i / steps, 2) if steps > 0 else 0,
                "coordinates": coords,
                "nearest_garment": nearest[0][0] if nearest else None,
                "nearest_distance": round(nearest[0][1], 4) if nearest else None,
            })
        
        return {
            "from": garment_a,
            "to": garment_b,
            "steps": steps,
            "total_distance": round(euclidean_distance(ga["coordinates"], gb["coordinates"]), 4),
            "waypoints": waypoints,
        }
    
    @mcp.tool()
    def decompose_garment_intent(description: str) -> dict:
        """Decompose natural language into garment 7D coordinates via keyword matching.
        
        Layer 2: Deterministic classification (0 tokens).
        
        Args:
            description: Natural language (e.g. "flowing dramatic red carpet gown",
                         "tough structured streetwear", "ethereal sheer romantic")
        
        Returns matching garments and fabrics ranked by keyword overlap.
        """
        index = get_keyword_index_data()
        tokens = tokenize_intent(description)
        
        if not tokens:
            return {"error": "No meaningful keywords found", "description": description}
        
        # Search garments
        garment_matches = search_by_keywords(tokens, index, source_type="garment")
        fabric_matches = search_by_keywords(tokens, index, source_type="fabric")
        
        # Get coordinates for top garment match
        catalog = get_garment_catalog()
        top_garment = None
        if garment_matches:
            gname = garment_matches[0]["source"]
            g = catalog.get(gname)
            if g:
                top_garment = {
                    "name": gname,
                    "coordinates": g["coordinates"],
                    "category": g["category"],
                }
        
        return {
            "description": description,
            "tokens": tokens,
            "garment_matches": garment_matches[:5],
            "fabric_matches": fabric_matches[:3],
            "top_garment": top_garment,
        }
