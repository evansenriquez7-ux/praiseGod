"""
matatag_loader.py
-----------------
Loads MATATAG (Philippine K-10 Math Curriculum) competencies into the skill_nodes table.

Structure of MATATAG:
- Grade 1-10
- 3 Content Areas: Number and Algebra, Measurement and Geometry, Data and Probability
- 4 Quarters per grade
- Multiple competencies per quarter

Node ID format: mat_g{grade}_{area_code}_q{quarter}_{index}
  - area_code: na (Number and Algebra), mg (Measurement and Geometry), dp (Data and Probability)

Usage:
    from matatag_loader import load_matatag_curriculum
    load_matatag_curriculum(db)  # Populates skill_nodes with MATATAG nodes
"""

import json
import os
from sqlalchemy.orm import Session
from typing import Optional

# Map content area names to short codes
AREA_CODES = {
    "Number and Algebra": "na",
    "Measurement and Geometry": "mg",
    "Data and Probability": "dp",
}

# Reverse mapping for display
AREA_NAMES = {v: k for k, v in AREA_CODES.items()}


def _get_matatag_data_path() -> str:
    """Get path to matatagmath.json file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "ph", "matatagmath.json")


def _load_matatag_json() -> dict:
    """Load and return the MATATAG curriculum JSON."""
    path = _get_matatag_data_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[MATATAG Loader] ERROR: File not found: {path}")
        return {}
    except Exception as e:
        print(f"[MATATAG Loader] ERROR loading {path}: {e}")
        return {}


def generate_node_id(grade: int, area_code: str, quarter: int, index: int) -> str:
    """Generate a unique node ID for a MATATAG competency."""
    return f"mat_g{grade}_{area_code}_q{quarter}_{index}"


def parse_node_id(node_id: str) -> Optional[dict]:
    """
    Parse a MATATAG node ID back into its components.
    
    Returns:
        dict with grade, area_code, quarter, index or None if invalid
    """
    if not node_id.startswith("mat_"):
        return None
    
    try:
        parts = node_id.split("_")
        if len(parts) != 5:
            return None
        
        grade = int(parts[1][1:])  # Remove 'g' prefix
        area_code = parts[2]
        quarter = int(parts[3][1:])  # Remove 'q' prefix
        index = int(parts[4])
        
        return {
            "grade": grade,
            "area_code": area_code,
            "area_name": AREA_NAMES.get(area_code, area_code),
            "quarter": quarter,
            "index": index,
        }
    except (ValueError, IndexError):
        return None


def load_matatag_curriculum(db: Session, clear_existing: bool = False) -> dict:
    """
    Load MATATAG curriculum into skill_nodes table.
    
    Args:
        db: SQLAlchemy database session
        clear_existing: If True, delete all existing MATATAG nodes before loading
        
    Returns:
        dict with counts: {"loaded": N, "skipped": N, "errors": N}
    """
    from backend.app import models
    
    stats = {"loaded": 0, "skipped": 0, "errors": 0}
    
    if clear_existing:
        deleted = db.query(models.SkillNode).filter(
            models.SkillNode.id.like("mat_%")
        ).delete(synchronize_session=False)
        db.commit()
        print(f"[MATATAG Loader] Cleared {deleted} existing MATATAG nodes")
    
    data = _load_matatag_json()
    if not data:
        return stats
    
    # Navigate: Mathematics -> Grade X -> Content Area -> Quarter -> Competencies
    math_data = data.get("Mathematics", data)
    
    for grade_key in sorted(math_data.keys(), key=lambda x: int(x.split()[-1]) if x.split()[-1].isdigit() else 0):
        # Extract grade number from "Grade 1", "Grade 2", etc.
        try:
            grade = int(grade_key.split()[-1])
        except ValueError:
            continue
        
        grade_data = math_data[grade_key]
        if not isinstance(grade_data, dict):
            continue
        
        for content_area, area_data in grade_data.items():
            area_code = AREA_CODES.get(content_area)
            if not area_code:
                print(f"[MATATAG Loader] Unknown content area: {content_area}")
                continue
            
            if not isinstance(area_data, dict):
                continue
            
            for quarter_key, competencies in area_data.items():
                # Parse quarter from "Quarter 1", "Q1", etc.
                quarter = None
                if "Quarter" in quarter_key:
                    try:
                        quarter = int(quarter_key.split()[-1])
                    except ValueError:
                        pass
                elif quarter_key.startswith("Q"):
                    try:
                        quarter = int(quarter_key[1:])
                    except ValueError:
                        pass
                
                if quarter is None:
                    continue
                
                if not isinstance(competencies, list):
                    continue
                
                for index, comp in enumerate(competencies, start=0):
                    # Handle both string and dict competency formats
                    if isinstance(comp, str):
                        competency_text = comp
                        metadata = {}
                    elif isinstance(comp, dict):
                        competency_text = comp.get("competency") or comp.get("description") or str(comp)
                        metadata = {k: v for k, v in comp.items() if k not in ["competency", "description"]}
                    else:
                        continue
                    
                    node_id = generate_node_id(grade, area_code, quarter, index)
                    
                    # Check if node already exists
                    existing = db.query(models.SkillNode).filter(models.SkillNode.id == node_id).first()
                    if existing:
                        stats["skipped"] += 1
                        continue
                    
                    try:
                        node = models.SkillNode(
                            id=node_id,
                            statement_code=node_id,
                            title=competency_text[:500],  # Truncate if too long
                            description=competency_text,
                            grade_level=str(grade),
                            subject="Matatag",
                            metadata_json={
                                "content_area": content_area,
                                "area_code": area_code,
                                "quarter": quarter,
                                "index": index,
                                **metadata
                            }
                        )
                        db.add(node)
                        stats["loaded"] += 1
                    except Exception as e:
                        print(f"[MATATAG Loader] Error adding {node_id}: {e}")
                        stats["errors"] += 1
    
    db.commit()
    print(f"[MATATAG Loader] Loaded {stats['loaded']} nodes, skipped {stats['skipped']}, errors {stats['errors']}")
    return stats


def get_competency_by_id(node_id: str, db: Session) -> Optional[dict]:
    """
    Get a MATATAG competency by its node ID.
    
    Returns:
        dict with node details or None if not found
    """
    from backend.app import models
    
    node = db.query(models.SkillNode).filter(models.SkillNode.id == node_id).first()
    if not node:
        return None
    
    parsed = parse_node_id(node_id)
    
    return {
        "id": node.id,
        "title": node.title,
        "description": node.description,
        "grade": node.grade_level,
        "subject": node.subject,
        "content_area": parsed.get("area_name") if parsed else None,
        "quarter": parsed.get("quarter") if parsed else None,
        "metadata": node.metadata_json or {},
    }


def get_competencies_for_grade(grade: int, db: Session, content_area: Optional[str] = None) -> list:
    """
    Get all MATATAG competencies for a grade level.
    
    Args:
        grade: Grade level (1-10)
        db: Database session
        content_area: Optional filter by content area name
        
    Returns:
        List of competency dicts
    """
    from backend.app import models
    
    query = db.query(models.SkillNode).filter(
        models.SkillNode.id.like("mat_%"),
        models.SkillNode.grade_level == str(grade)
    )
    
    if content_area:
        area_code = AREA_CODES.get(content_area)
        if area_code:
            query = query.filter(models.SkillNode.id.like(f"mat_g{grade}_{area_code}_%"))
    
    nodes = query.all()
    
    results = []
    for node in nodes:
        parsed = parse_node_id(node.id)
        results.append({
            "id": node.id,
            "title": node.title,
            "grade": grade,
            "content_area": parsed.get("area_name") if parsed else None,
            "quarter": parsed.get("quarter") if parsed else None,
            "index": parsed.get("index") if parsed else None,
        })
    
    # Sort by quarter, then index
    results.sort(key=lambda x: (x.get("quarter", 0), x.get("index", 0)))
    
    return results


# CLI interface for standalone loading
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from backend.app.database import SessionLocal
    
    db = SessionLocal()
    try:
        clear = "--clear" in sys.argv
        stats = load_matatag_curriculum(db, clear_existing=clear)
        print(f"Done: {stats}")
    finally:
        db.close()
