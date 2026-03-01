"""
Fabric physics computation for garment-dynamics.
Deterministic calculation of how fabric properties modify garment behavior.
"""


def compute_fabric_coordinate_shift(garment_coords: dict, fabric: dict) -> dict:
    """Compute how fabric physics shift a garment's 7D coordinates.
    
    Fabric properties create deterministic shifts:
    - Heavy fabrics increase volume (weight of fall)
    - High drape reduces structural rigidity
    - Low recovery increases surface activity (wrinkles)
    - High recovery maintains clean surface
    """
    shifts = {}
    
    weight = fabric.get("weight", 0.3)
    drape = fabric.get("drape_coefficient", 0.5)
    recovery = fabric.get("recovery", 0.5)
    
    # Volume: heavy drapy fabrics add volume through fall; stiff light fabrics reduce
    volume_shift = (weight - 0.3) * 0.15 + (drape - 0.5) * 0.10
    shifts["silhouette_volume"] = round(volume_shift, 4)
    
    # Rigidity: high drape reduces structure; low drape adds
    rigidity_shift = -(drape - 0.5) * 0.25
    shifts["structural_rigidity"] = round(rigidity_shift, 4)
    
    # Surface activity: low recovery = wrinkles = more activity
    surface_shift = -(recovery - 0.5) * 0.15
    # Visible texture fabrics also add activity
    surface_terms = fabric.get("surface", "")
    if any(t in surface_terms for t in ["texture", "weave", "pile", "net", "disc"]):
        surface_shift += 0.10
    shifts["surface_activity"] = round(surface_shift, 4)
    
    # Construction complexity unaffected by fabric
    shifts["construction_complexity"] = 0.0
    
    # Hem geometry: heavy fabrics pool more, stiff fabrics maintain edge
    hem_shift = (weight - 0.3) * 0.08 + (drape - 0.5) * 0.05
    shifts["hem_geometry"] = round(hem_shift, 4)
    
    # Exposure: sheer fabrics effectively increase
    if "transparent" in surface_terms or "semi-transparent" in surface_terms:
        shifts["exposure_ratio"] = 0.15
    else:
        shifts["exposure_ratio"] = 0.0
    
    # Temporal register unaffected
    shifts["temporal_register"] = 0.0
    
    return shifts


def apply_fabric_shifts(garment_coords: dict, shifts: dict) -> dict:
    """Apply fabric shifts to garment coordinates, clamping to [0, 1]."""
    result = {}
    for param, val in garment_coords.items():
        shift = shifts.get(param, 0.0)
        result[param] = max(0.0, min(1.0, round(val + shift, 4)))
    return result


def compute_drape_behavior(garment: dict, fabric: dict) -> dict:
    """Compute specific drape behavior from garment + fabric combination."""
    drape_coeff = fabric.get("drape_coefficient", 0.5)
    weight = fabric.get("weight", 0.3)
    recovery = fabric.get("recovery", 0.5)
    
    garment_fb = garment.get("fabric_behavior", {})
    base_drape = garment_fb.get("drape_character", "moderate")
    
    # Drape intensity
    if drape_coeff > 0.75:
        drape_quality = "liquid-flowing"
    elif drape_coeff > 0.50:
        drape_quality = "soft-falling"
    elif drape_coeff > 0.25:
        drape_quality = "moderate-controlled"
    else:
        drape_quality = "stiff-holding"
    
    # Fold depth from weight
    if weight > 0.60:
        fold_depth = "deep-sculptural"
    elif weight > 0.35:
        fold_depth = "medium-defined"
    else:
        fold_depth = "shallow-fine"
    
    # Fold permanence from recovery
    if recovery < 0.20:
        fold_permanence = "permanent-creases"
    elif recovery < 0.50:
        fold_permanence = "semi-permanent-holds-shape"
    else:
        fold_permanence = "temporary-springs-back"
    
    return {
        "drape_quality": drape_quality,
        "fold_depth": fold_depth,
        "fold_permanence": fold_permanence,
        "base_drape": base_drape,
        "fabric_fold_character": fabric.get("fold_character", ""),
        "combined_description": f"{drape_quality} with {fold_depth} folds, {fold_permanence}",
    }


def compute_light_on_fabric(fabric: dict, color_data: dict = None) -> dict:
    """Compute light interaction properties for a fabric + optional color."""
    light = fabric.get("light_interaction", "")
    surface = fabric.get("surface", "")
    
    # Determine sheen category
    if any(t in surface for t in ["sheen", "reflective", "smooth"]):
        sheen = "high"
    elif any(t in surface for t in ["matte", "texture", "weave"]):
        sheen = "low"
    else:
        sheen = "moderate"
    
    result = {
        "light_interaction": light,
        "surface_character": surface,
        "sheen_category": sheen,
    }
    
    if color_data:
        fabric_key = "high_sheen" if sheen == "high" else ("matte" if sheen == "low" else "matte")
        fi = color_data.get("fabric_interactions", {})
        result["color_on_fabric"] = fi.get(fabric_key, "")
        result["shadow_color"] = color_data.get("shadow_behavior", "")
        result["highlight_color"] = color_data.get("highlight_behavior", "")
        result["volume_effect"] = color_data.get("volume_effect", "")
    
    return result


def compute_form_behavior(garment: dict, fabric: dict, form: dict, environment: str = "still") -> dict:
    """Compute garment behavior on a specific form in an environment."""
    drape_coeff = fabric.get("drape_coefficient", 0.5)
    weight = fabric.get("weight", 0.3)
    
    form_drape = form.get("drape_behavior", "")
    form_supports = form.get("support_points", [])
    body_present = form.get("body_present", True)
    
    garment_sil = garment.get("silhouette_geometry", {})
    garment_fb = garment.get("fabric_behavior", {})
    
    # Silhouette: depends on form
    if not body_present:
        if "flat" in form.get("gravity_anchor", ""):
            silhouette = "collapsed-flat-spread"
        elif "suspended" in form.get("gravity_anchor", ""):
            silhouette = f"gravity-fall-from-{len(form_supports)}-points"
        else:
            silhouette = "draped-over-form-cascading"
    else:
        silhouette = garment_sil.get("primary_outline", "body-contour")
    
    # Environment effect
    env_effects = {
        "still": "static-gravity-only",
        "light_breeze": "gentle-lift-at-hems-and-loose-edges",
        "strong_wind": "dramatic-billow-and-snap-fabric-airborne",
        "underwater": "full-float-slow-motion-all-fabric-suspended",
        "zero_gravity": "all-fabric-floating-spherical-distribution",
    }
    env_effect = env_effects.get(environment, "static-gravity-only")
    
    # Motion activation
    if environment != "still":
        motion_response = garment_fb.get("motion_response", "")
        if drape_coeff > 0.7:
            env_fabric = "high-response-fluid-reaction"
        elif drape_coeff > 0.3:
            env_fabric = "moderate-response-delayed-swing"
        else:
            env_fabric = "minimal-response-holds-shape"
    else:
        motion_response = "none-static"
        env_fabric = "no-environmental-activation"
    
    return {
        "silhouette": silhouette,
        "form_description": form_drape,
        "support_points": form_supports,
        "body_present": body_present,
        "environment_effect": env_effect,
        "fabric_environment_response": env_fabric,
        "static_fold_pattern": garment_fb.get("fold_pattern", ""),
        "gravity_response": garment_fb.get("gravity_response", ""),
        "compositional_weight": garment_sil.get("visual_weight", ""),
    }
