"""
Comprehensive test suite for garment-dynamics MCP server.
"""

import json
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

PASSED = 0
FAILED = 0


def test(name):
    global PASSED, FAILED
    print(f"\n[TEST] {name}")
    try:
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        FAILED += 1
        return False


def passed():
    global PASSED
    print("  ✓ PASSED")
    PASSED += 1


def failed(msg):
    global FAILED
    print(f"  ✗ FAILED: {msg}")
    FAILED += 1


# ============================================================
# TEST 1: Data Loading
# ============================================================
print("\n[TEST] Data Loading")
try:
    from layers.taxonomy import _load_data, get_garment_catalog, get_fabric_catalog
    from layers.taxonomy import get_color_catalog, get_form_catalog, get_vocabulary_data
    from layers.taxonomy import get_keyword_index_data
    
    _load_data()
    garments = get_garment_catalog()
    fabrics = get_fabric_catalog()
    colors = get_color_catalog()
    forms = get_form_catalog()
    vocab = get_vocabulary_data()
    kw_index = get_keyword_index_data()
    
    print(f"  Loading garment catalog... OK ({len(garments)} garments)")
    print(f"  Loading fabric physics... OK ({len(fabrics)} fabrics)")
    print(f"  Loading color interactions... OK ({len(colors)} colors)")
    print(f"  Loading form types... OK ({len(forms)} forms)")
    print(f"  Loading vocabulary... OK ({len(vocab)} categories)")
    print(f"  Building keyword index... OK ({len(kw_index)} keywords)")
    
    assert len(garments) >= 20, f"Expected >= 20 garments, got {len(garments)}"
    assert len(fabrics) >= 10, f"Expected >= 10 fabrics, got {len(fabrics)}"
    assert len(colors) >= 8, f"Expected >= 8 colors, got {len(colors)}"
    assert len(forms) >= 7, f"Expected >= 7 forms, got {len(forms)}"
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 2: Garment Completeness
# ============================================================
print("\n[TEST] Garment Completeness")
try:
    required_fields = ["category", "coordinates", "construction", "fabric_behavior",
                       "silhouette_geometry", "keywords"]
    coord_params = ["silhouette_volume", "structural_rigidity", "construction_complexity",
                    "surface_activity", "hem_geometry", "exposure_ratio", "temporal_register"]
    
    errors = []
    for name, garment in garments.items():
        for field in required_fields:
            if field not in garment:
                errors.append(f"{name} missing '{field}'")
        
        coords = garment.get("coordinates", {})
        for param in coord_params:
            if param not in coords:
                errors.append(f"{name} missing coordinate '{param}'")
            else:
                val = coords[param]
                if not (0.0 <= val <= 1.0):
                    errors.append(f"{name}.{param} = {val} out of [0,1]")
    
    if errors:
        for e in errors[:5]:
            print(f"  ERROR: {e}")
        failed(f"{len(errors)} completeness errors")
    else:
        print(f"  All {len(garments)} garments have complete fields")
        passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 3: Fabric Physics Completeness
# ============================================================
print("\n[TEST] Fabric Physics Completeness")
try:
    required = ["weight", "drape_coefficient", "recovery", "surface",
                "light_interaction", "fold_character", "keywords"]
    errors = []
    for name, fabric in fabrics.items():
        for field in required:
            if field not in fabric:
                errors.append(f"{name} missing '{field}'")
        
        # Range checks
        for num_field in ["weight", "drape_coefficient", "recovery"]:
            val = fabric.get(num_field, -1)
            if not (0.0 <= val <= 1.0):
                errors.append(f"{name}.{num_field} = {val} out of [0,1]")
    
    if errors:
        for e in errors[:5]:
            print(f"  ERROR: {e}")
        failed(f"{len(errors)} fabric errors")
    else:
        print(f"  All {len(fabrics)} fabrics complete and in range")
        passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 4: Coordinate Math
# ============================================================
print("\n[TEST] Coordinate Math")
try:
    from utils.coordinates import euclidean_distance, interpolate, find_nearest
    
    # Self-distance = 0
    slip = garments["slip_dress"]["coordinates"]
    assert euclidean_distance(slip, slip) == 0.0, "Self-distance should be 0"
    
    # Triangle inequality
    a = garments["slip_dress"]["coordinates"]
    b = garments["ball_gown"]["coordinates"]
    c = garments["leather_jacket"]["coordinates"]
    d_ab = euclidean_distance(a, b)
    d_bc = euclidean_distance(b, c)
    d_ac = euclidean_distance(a, c)
    assert d_ac <= d_ab + d_bc + 0.0001, "Triangle inequality violated"
    
    # Interpolation endpoints
    traj = interpolate(a, b, steps=5)
    assert len(traj) == 6, f"Expected 6 points, got {len(traj)}"
    assert euclidean_distance(traj[0], a) < 0.001, "Interpolation start != a"
    assert euclidean_distance(traj[-1], b) < 0.001, "Interpolation end != b"
    
    # Nearest neighbor
    nearest = find_nearest(a, garments, max_results=3, exclude="slip_dress")
    assert len(nearest) == 3, f"Expected 3 nearest, got {len(nearest)}"
    assert nearest[0][1] <= nearest[1][1], "Nearest not sorted"
    
    print("  Coordinate math: distance, interpolation, nearest-neighbor OK")
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 5: Modifiers
# ============================================================
print("\n[TEST] Modifiers")
try:
    from utils.coordinates import apply_modifier
    
    base = garments["blazer"]["coordinates"]
    
    # Oversized should increase volume
    oversized = apply_modifier(base, "oversized")
    assert oversized["silhouette_volume"] > base["silhouette_volume"], \
        "Oversized should increase volume"
    
    # Fitted should decrease volume
    fitted = apply_modifier(base, "fitted")
    assert fitted["silhouette_volume"] < base["silhouette_volume"], \
        "Fitted should decrease volume"
    
    # All values stay in [0, 1]
    for mod in ["oversized", "cropped", "fitted", "elongated", "distressed"]:
        result = apply_modifier(base, mod)
        for param, val in result.items():
            assert 0.0 <= val <= 1.0, f"{mod}.{param} = {val} out of range"
    
    print("  Modifiers: all 5 types validated, ranges OK")
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 6: Fabric Physics Computation
# ============================================================
print("\n[TEST] Fabric Physics Computation")
try:
    from utils.fabric_physics import (
        compute_fabric_coordinate_shift, apply_fabric_shifts,
        compute_drape_behavior, compute_light_on_fabric, compute_form_behavior,
    )
    
    base_coords = garments["ball_gown"]["coordinates"]
    
    # Silk should make it drapier
    silk = fabrics["silk_charmeuse"]
    silk_shifts = compute_fabric_coordinate_shift(base_coords, silk)
    assert silk_shifts["structural_rigidity"] < 0, \
        "High-drape silk should reduce rigidity"
    
    # Leather should add rigidity
    leather_fab = fabrics["leather"]
    leather_shifts = compute_fabric_coordinate_shift(base_coords, leather_fab)
    assert leather_shifts["structural_rigidity"] > 0, \
        "Low-drape leather should increase rigidity"
    
    # Apply shifts stays in range
    modified = apply_fabric_shifts(base_coords, silk_shifts)
    for param, val in modified.items():
        assert 0.0 <= val <= 1.0, f"Modified {param} = {val} out of range"
    
    # Drape behavior
    drape = compute_drape_behavior(garments["slip_dress"], silk)
    assert "liquid" in drape["drape_quality"], \
        f"Silk on slip should be liquid, got {drape['drape_quality']}"
    
    # Light on fabric
    light = compute_light_on_fabric(silk)
    assert light["sheen_category"] in ("high", "moderate", "low")
    
    print("  Fabric physics: shifts, drape, light all validated")
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 7: Keyword Index
# ============================================================
print("\n[TEST] Keyword Index")
try:
    from utils.keyword_index import tokenize_intent, search_by_keywords
    
    # Tokenization removes stop words
    tokens = tokenize_intent("a dramatic flowing red carpet gown")
    assert "a" not in tokens, "Stop word 'a' not removed"
    assert "dramatic" in tokens, "'dramatic' should survive tokenization"
    
    # Search returns results
    matches = search_by_keywords(tokens, kw_index, source_type="garment")
    assert len(matches) > 0, "Should find garment matches for 'dramatic flowing'"
    
    # Top match should be reasonable
    top = matches[0]["source"]
    print(f"  Intent 'dramatic flowing red carpet gown' → top match: {top}")
    
    # Fabric search
    fabric_tokens = tokenize_intent("luxury liquid glamour")
    fabric_matches = search_by_keywords(fabric_tokens, kw_index, source_type="fabric")
    assert len(fabric_matches) > 0, "Should find fabric matches"
    print(f"  Intent 'luxury liquid glamour' → top fabric: {fabric_matches[0]['source']}")
    
    print(f"  Keyword index: {len(kw_index)} keywords, decomposition OK")
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 8: Categories
# ============================================================
print("\n[TEST] Categories")
try:
    cats = {}
    for name, garment in garments.items():
        c = garment["category"]
        cats[c] = cats.get(c, 0) + 1
    
    print(f"  Categories: {cats}")
    
    expected_cats = {"dresses", "tailored", "flowing", "tops", "bottoms", 
                     "outerwear", "avant_garde"}
    for ec in expected_cats:
        assert ec in cats, f"Missing expected category: {ec}"
    
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 9: Form Types
# ============================================================
print("\n[TEST] Form Types")
try:
    # Body-present forms
    body_forms = [n for n, f in forms.items() if f.get("body_present")]
    no_body_forms = [n for n, f in forms.items() if not f.get("body_present")]
    
    print(f"  Body-present forms: {body_forms}")
    print(f"  No-body forms: {no_body_forms}")
    
    assert len(body_forms) >= 3, "Should have >= 3 body-present forms"
    assert len(no_body_forms) >= 4, "Should have >= 4 no-body forms"
    
    # Form behavior computation
    form_data = forms["hanger"]
    gown = garments["ball_gown"]
    generic_fabric = {
        "weight": 0.35, "drape_coefficient": 0.50, "recovery": 0.40,
        "surface": "moderate", "fold_character": "medium",
    }
    result = compute_form_behavior(gown, generic_fabric, form_data, "still")
    assert "gravity-fall" in result["silhouette"] or "collapsed" in result["silhouette"] or "gravity" in result["silhouette"].lower() or "point" in result["silhouette"], \
        f"Gown on hanger should show gravity fall, got: {result['silhouette']}"
    
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 10: Color Interactions
# ============================================================
print("\n[TEST] Color Interactions")
try:
    required_color_fields = ["value", "volume_effect", "shadow_behavior",
                              "highlight_behavior", "mood", "fabric_interactions"]
    errors = []
    for name, color in colors.items():
        for field in required_color_fields:
            if field not in color:
                errors.append(f"{name} missing '{field}'")
        
        fi = color.get("fabric_interactions", {})
        for fabric_type in ["high_sheen", "matte", "transparent"]:
            if fabric_type not in fi:
                errors.append(f"{name} missing fabric_interaction '{fabric_type}'")
    
    if errors:
        for e in errors[:5]:
            print(f"  ERROR: {e}")
        failed(f"{len(errors)} color errors")
    else:
        # Test color-fabric combination
        light = compute_light_on_fabric(fabrics["velvet"], colors["deep_emerald"])
        assert light.get("color_on_fabric"), "Should have color_on_fabric result"
        print(f"  Velvet + emerald: {light['color_on_fabric'][:60]}...")
        print(f"  All {len(colors)} colors complete with fabric interactions")
        passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 11: No Pose Domain Leakage
# ============================================================
print("\n[TEST] No Pose Domain Leakage")
try:
    pose_terms = {"contrapposto", "s_curve", "hip_displacement", "joint_articulation",
                  "weight_asymmetry", "gaze_deviation", "dynamic_tension",
                  "body_surface_map", "stretched_surfaces", "compressed_surfaces",
                  "motion_vectors"}
    
    catalog_str = json.dumps(garments).lower()
    leaks = []
    for term in pose_terms:
        if term in catalog_str:
            leaks.append(term)
    
    if leaks:
        failed(f"Pose domain leakage: {leaks}")
    else:
        print("  No pose domain leakage detected")
        passed()
except Exception as e:
    failed(str(e))


# ============================================================
# TEST 12: End-to-End Synthesis Pipeline
# ============================================================
print("\n[TEST] End-to-End Synthesis Pipeline")
try:
    from layers.synthesis import _resolve_garment, _resolve_fabric, _build_garment_spec
    
    # Resolve from intent
    g_name, garment = _resolve_garment("dramatic flowing red carpet gown", "", garments)
    assert g_name is not None, "Should resolve garment from intent"
    print(f"  Intent 'dramatic flowing red carpet gown' → {g_name}")
    
    # Resolve fabric from intent
    f_name, fabric = _resolve_fabric("liquid luxury glamour", "", fabrics)
    assert f_name is not None, "Should resolve fabric from intent"
    print(f"  Intent 'liquid luxury glamour' → {f_name}")
    
    # Build spec
    form_data = forms["standing_mannequin"]
    color_data = colors["red"]
    spec = _build_garment_spec(garment, fabric, color_data, form_data, "still")
    
    assert spec.get("primary_outline"), "Spec should have primary_outline"
    assert spec.get("drape_behavior"), "Spec should have drape_behavior"
    print(f"  Spec: outline={spec['primary_outline']}, drape={spec['drape_behavior'][:40]}...")
    
    passed()
except Exception as e:
    failed(str(e))


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 50)
print(f"Results: {PASSED} passed, {FAILED} failed out of {PASSED + FAILED}")

if FAILED > 0:
    sys.exit(1)
