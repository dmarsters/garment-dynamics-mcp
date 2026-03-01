"""
Layer 3: Structured data for Claude synthesis (~100-200 tokens).
Full pipeline: intent → garment → fabric → color → form → structured output.

Note: Garment-body composition happens via aesthetics-dynamics-core,
not within this server. This server provides garment geometry
independent of body pose.
"""

from layers.taxonomy import (
    get_garment_catalog, get_fabric_catalog, get_color_catalog,
    get_form_catalog, get_keyword_index_data,
)
from utils.coordinates import apply_modifier
from utils.keyword_index import tokenize_intent, search_by_keywords
from utils.fabric_physics import (
    compute_fabric_coordinate_shift, apply_fabric_shifts,
    compute_drape_behavior, compute_light_on_fabric, compute_form_behavior,
)


def _resolve_garment(intent: str, garment_name: str, catalog: dict) -> tuple:
    """Resolve garment from explicit name or intent decomposition."""
    if garment_name:
        garment = catalog.get(garment_name)
        if garment:
            return garment_name, garment
        return None, None
    
    # Decompose from intent
    index = get_keyword_index_data()
    tokens = tokenize_intent(intent)
    if not tokens:
        return None, None
    
    matches = search_by_keywords(tokens, index, source_type="garment")
    if matches:
        name = matches[0]["source"]
        return name, catalog.get(name)
    
    return None, None


def _resolve_fabric(intent: str, fabric_name: str, catalog: dict) -> tuple:
    """Resolve fabric from explicit name or intent decomposition."""
    if fabric_name:
        fabric = catalog.get(fabric_name)
        if fabric:
            return fabric_name, fabric
        return None, None
    
    # Try intent decomposition for fabric
    index = get_keyword_index_data()
    tokens = tokenize_intent(intent)
    if not tokens:
        return None, None
    
    matches = search_by_keywords(tokens, index, source_type="fabric")
    if matches:
        name = matches[0]["source"]
        return name, catalog.get(name)
    
    return None, None


def _build_garment_spec(garment: dict, fabric: dict, color_data: dict,
                         form_data: dict, environment: str) -> dict:
    """Build complete geometric specification for prompt synthesis."""
    spec = {}
    
    # Silhouette geometry
    sil = garment.get("silhouette_geometry", {})
    spec["primary_outline"] = sil.get("primary_outline", "")
    spec["negative_space"] = sil.get("negative_space", "")
    spec["width_variation"] = sil.get("width_variation", [])
    spec["visual_weight"] = sil.get("visual_weight", "")
    
    # Construction details
    con = garment.get("construction", {})
    spec["cut"] = con.get("cut", "")
    spec["closure"] = con.get("closure", "")
    spec["structural_elements"] = con.get("structural_elements", [])
    
    # Fabric behavior on this garment
    if fabric:
        drape = compute_drape_behavior(garment, fabric)
        spec["drape_behavior"] = drape["combined_description"]
        spec["fold_character"] = fabric.get("fold_character", "")
        spec["surface_character"] = fabric.get("surface", "")
        spec["light_interaction"] = fabric.get("light_interaction", "")
    else:
        fb = garment.get("fabric_behavior", {})
        spec["drape_behavior"] = fb.get("drape_character", "")
        spec["fold_character"] = fb.get("fold_pattern", "")
    
    # Color on fabric
    if color_data and fabric:
        light = compute_light_on_fabric(fabric, color_data)
        spec["color_on_fabric"] = light.get("color_on_fabric", "")
        spec["shadow_color"] = light.get("shadow_color", "")
        spec["highlight_color"] = light.get("highlight_color", "")
        spec["volume_effect"] = light.get("volume_effect", "")
    
    # Form behavior
    if form_data and fabric:
        form_b = compute_form_behavior(garment, fabric, form_data, environment)
        spec["form_silhouette"] = form_b["silhouette"]
        spec["environment_effect"] = form_b["environment_effect"]
        spec["gravity_response"] = form_b["gravity_response"]
    
    return spec


def register_synthesis_tools(mcp):
    """Register all Layer 3 tools on the MCP server."""
    
    @mcp.tool()
    def enhance_garment_prompt(
        intent: str,
        garment_name: str = "",
        fabric_name: str = "",
        color: str = "",
        form: str = "standing_mannequin",
        environment: str = "still",
        frame_aspect: str = "2:3",
        camera_distance: str = "full_body",
        intensity: float = 0.7,
    ) -> dict:
        """Full pipeline: intent + garment + fabric + color → structured data
        for Claude synthesis into image-generation prompt.
        
        Layer 3: Structured data (~100-200 tokens).
        
        Runs the full computation chain:
        1. Resolve garment (from name or intent decomposition)
        2. Apply fabric physics
        3. Apply color interaction
        4. Compute form behavior
        5. Compile geometric specification vocabulary
        
        Note: Garment-body pose composition happens externally via
        aesthetics-dynamics-core multi-domain composition. This server
        provides garment geometry independent of any body pose.
        
        Args:
            intent: Natural language description 
            garment_name: Explicit garment (overrides intent matching)
            fabric_name: Explicit fabric (overrides intent matching)
            color: Color name from color library
            form: Display form type
            environment: Environmental condition
            frame_aspect: Image aspect ratio
            camera_distance: "full_body", "three_quarter", "close_up", "detail"
            intensity: Enhancement intensity 0.0-1.0
        """
        garments = get_garment_catalog()
        fabrics = get_fabric_catalog()
        colors = get_color_catalog()
        forms = get_form_catalog()
        
        # 1. Resolve garment
        g_name, garment = _resolve_garment(intent, garment_name, garments)
        if not garment:
            return {
                "error": "Could not resolve garment",
                "intent": intent,
                "garment_name": garment_name,
                "available_garments": sorted(garments.keys()),
            }
        
        # 2. Resolve fabric
        f_name, fabric = _resolve_fabric(intent, fabric_name, fabrics)
        
        # 3. Resolve color
        color_data = colors.get(color) if color else None
        
        # 4. Resolve form
        form_data = forms.get(form, forms.get("standing_mannequin"))
        
        # 5. Compute modified coordinates
        if fabric:
            shifts = compute_fabric_coordinate_shift(garment["coordinates"], fabric)
            modified_coords = apply_fabric_shifts(garment["coordinates"], shifts)
        else:
            modified_coords = dict(garment["coordinates"])
        
        # 6. Build geometric spec
        spec = _build_garment_spec(garment, fabric, color_data, form_data, environment)
        
        # 7. Frame and camera
        frame_spec = {
            "aspect_ratio": frame_aspect,
            "camera_distance": camera_distance,
        }
        
        # Camera framing guidance
        if camera_distance == "full_body":
            frame_spec["framing"] = "full garment visible head to hem"
        elif camera_distance == "three_quarter":
            frame_spec["framing"] = "hip to head, hem implied"
        elif camera_distance == "close_up":
            frame_spec["framing"] = "detail of fabric, construction, texture"
        elif camera_distance == "detail":
            frame_spec["framing"] = "extreme close on surface, thread, texture"
        
        return {
            "garment": g_name,
            "fabric": f_name,
            "color": color or None,
            "form": form,
            "environment": environment,
            "intensity": intensity,
            "coordinates": modified_coords,
            "geometric_specification": spec,
            "frame": frame_spec,
            "keywords": garment.get("keywords", []),
            "domain_id": "garment_dynamics",
            "parameter_names": list(modified_coords.keys()),
            "composition_note": (
                "Garment-body interaction computed via aesthetics-dynamics-core. "
                "Use fashion-pose-dynamics body_surface_map with these garment "
                "coordinates for composed garment-on-body prompts."
            ),
        }
