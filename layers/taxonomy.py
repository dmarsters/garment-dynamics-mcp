"""
Layer 1: Pure taxonomy lookup (0 tokens).
Catalog access for garments, fabrics, forms, vocabulary, keywords.
"""

import json
import os

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

_garment_catalog = None
_fabric_catalog = None
_color_catalog = None
_form_catalog = None
_vocabulary = None
_keyword_index = None


def _load_data():
    """Load all data catalogs."""
    global _garment_catalog, _fabric_catalog, _color_catalog
    global _form_catalog, _vocabulary, _keyword_index
    
    if _garment_catalog is not None:
        return
    
    with open(os.path.join(_DATA_DIR, "garment_catalog.json")) as f:
        _garment_catalog = json.load(f)["garments"]
    
    with open(os.path.join(_DATA_DIR, "fabric_physics.json")) as f:
        _fabric_catalog = json.load(f)["fabrics"]
    
    with open(os.path.join(_DATA_DIR, "color_interactions.json")) as f:
        _color_catalog = json.load(f)["colors"]
    
    with open(os.path.join(_DATA_DIR, "form_types.json")) as f:
        _form_catalog = json.load(f)["forms"]
    
    with open(os.path.join(_DATA_DIR, "visual_vocabulary.json")) as f:
        _vocabulary = json.load(f)["vocabulary"]
    
    from utils.keyword_index import build_keyword_index
    _keyword_index = build_keyword_index(_garment_catalog, _fabric_catalog)


def get_garment_catalog():
    _load_data()
    return _garment_catalog

def get_fabric_catalog():
    _load_data()
    return _fabric_catalog

def get_color_catalog():
    _load_data()
    return _color_catalog

def get_form_catalog():
    _load_data()
    return _form_catalog

def get_vocabulary_data():
    _load_data()
    return _vocabulary

def get_keyword_index_data():
    _load_data()
    return _keyword_index


def register_taxonomy_tools(mcp):
    """Register all Layer 1 tools on the MCP server."""
    
    from utils.coordinates import apply_modifier
    
    @mcp.tool()
    def get_garment(garment_name: str, modifier: str = "") -> dict:
        """Look up a specific garment by name and return its complete specification.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Args:
            garment_name: Canonical name (e.g. "ball_gown", "leather_jacket", "slip_dress")
            modifier: Optional — "oversized", "cropped", "fitted", "elongated", "distressed"
        
        Returns full 7D coordinates, construction, fabric behavior,
        silhouette geometry, and keywords.
        """
        catalog = get_garment_catalog()
        garment = catalog.get(garment_name)
        if not garment:
            return {"error": f"Garment '{garment_name}' not found", 
                    "available": sorted(catalog.keys())}
        
        result = dict(garment)
        result["name"] = garment_name
        
        if modifier:
            result["coordinates"] = apply_modifier(garment["coordinates"], modifier)
            result["modifier_applied"] = modifier
        
        return result
    
    @mcp.tool()
    def list_garments(category: str = "", sort_by: str = "") -> dict:
        """List all garments with coordinates, optionally filtered by category.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Args:
            category: "dresses", "tailored", "flowing", "tops", "bottoms",
                      "outerwear", "avant_garde" (empty = all)
            sort_by: Any parameter name (e.g. "silhouette_volume")
        """
        catalog = get_garment_catalog()
        
        items = []
        for name, garment in catalog.items():
            if category and garment.get("category") != category:
                continue
            items.append({
                "name": name,
                "category": garment["category"],
                "coordinates": garment["coordinates"],
                "keywords": garment.get("keywords", []),
            })
        
        if sort_by:
            items.sort(key=lambda x: x["coordinates"].get(sort_by, 0), reverse=True)
        
        categories = {}
        for item in items:
            c = item["category"]
            categories[c] = categories.get(c, 0) + 1
        
        return {
            "count": len(items),
            "categories": categories,
            "garments": items,
        }
    
    @mcp.tool()
    def get_fabric(fabric_name: str) -> dict:
        """Look up fabric physics properties.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Args:
            fabric_name: e.g. "silk_charmeuse", "leather", "tulle", "velvet"
        
        Returns weight, drape coefficient, recovery, surface properties,
        light interaction, fold character, keywords.
        """
        catalog = get_fabric_catalog()
        fabric = catalog.get(fabric_name)
        if not fabric:
            return {"error": f"Fabric '{fabric_name}' not found",
                    "available": sorted(catalog.keys())}
        
        result = dict(fabric)
        result["name"] = fabric_name
        return result
    
    @mcp.tool()
    def list_fabrics(sort_by: str = "") -> dict:
        """List all fabric types with physics properties.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Args:
            sort_by: "weight", "drape_coefficient", "recovery"
        """
        catalog = get_fabric_catalog()
        
        items = []
        for name, fabric in catalog.items():
            items.append({
                "name": name,
                "weight": fabric["weight"],
                "drape_coefficient": fabric["drape_coefficient"],
                "recovery": fabric["recovery"],
                "keywords": fabric.get("keywords", []),
            })
        
        if sort_by and sort_by in ("weight", "drape_coefficient", "recovery"):
            items.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        
        return {"count": len(items), "fabrics": items}
    
    @mcp.tool()
    def get_garment_vocabulary() -> dict:
        """Return complete garment visual vocabulary organized by category.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Categories: silhouette_shapes, construction_elements, fabric_behaviors,
        fold_patterns, closure_types, structural_elements, hem_shapes,
        drape_descriptors, light_surface_terms.
        """
        return get_vocabulary_data()
    
    @mcp.tool()
    def get_keywords(garment_name: str = "", category: str = "") -> dict:
        """Return keyword associations for garments.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Args:
            garment_name: Specific garment for keyword list
            category: Keyword category — "mood", "era", "designer",
                      "occasion", "silhouette", "fabric_mood"
        
        If both empty, returns complete keyword index.
        """
        from utils.keyword_index import get_keywords_for_garment, get_keywords_by_category
        
        if garment_name:
            catalog = get_garment_catalog()
            garment = catalog.get(garment_name)
            if not garment:
                return {"error": f"Garment '{garment_name}' not found"}
            return {"garment": garment_name, "keywords": get_keywords_for_garment(garment)}
        
        if category:
            return {"category": category, "keywords": get_keywords_by_category(category)}
        
        index = get_keyword_index_data()
        return {"total_keywords": len(index), "sample": sorted(list(index.keys()))[:50]}
    
    @mcp.tool()
    def get_form_types() -> dict:
        """Return all display form types for garment-without-body computation.
        
        Layer 1: Pure taxonomy lookup (0 tokens).
        
        Forms include: standing_mannequin, dress_form, hanger, flat_lay,
        draped_on_chair, pooled_on_floor, wind_blown, on_body_walking,
        on_body_seated.
        """
        catalog = get_form_catalog()
        result = {}
        for name, form in catalog.items():
            result[name] = {
                "body_present": form.get("body_present"),
                "articulation": form.get("articulation"),
                "typical_use": form.get("typical_use"),
            }
        return result
