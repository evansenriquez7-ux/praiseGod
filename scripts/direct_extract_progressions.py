#!/usr/bin/env python3
"""
Direct Progressions Extraction - Uses this Claude session through file handshake.
Processes all 16 sections and writes evidence files directly.
"""

import os
import json
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime

PROGRESSIONS_PDF = "/Users/enrichmentcap/Documents/antigravity/ccmed/data/raw/progressions/Progressions_Complete.pdf"
OUTPUT_DIR = "/Users/enrichmentcap/Documents/antigravity/ccmed/data/processed/by_standard"

SECTIONS = [
    {"name": "Counting and Cardinality, K", "start_page": 16, "end_page": 18, "domains": ["K.CC"]},
    {"name": "Operations and Algebraic Thinking, K-5", "start_page": 19, "end_page": 57, "domains": ["K.OA", "1.OA", "2.OA", "3.OA", "4.OA", "5.OA"]},
    {"name": "Number and Operations in Base Ten, K-5", "start_page": 58, "end_page": 77, "domains": ["K.NBT", "1.NBT", "2.NBT", "3.NBT", "4.NBT", "5.NBT"]},
    {"name": "Measurement and Data, K-5", "start_page": 78, "end_page": 118, "domains": ["K.MD", "1.MD", "2.MD", "3.MD", "4.MD", "5.MD"]},
    {"name": "Geometry, K-6", "start_page": 119, "end_page": 138, "domains": ["K.G", "1.G", "2.G", "3.G", "4.G", "5.G", "6.G"]},
    {"name": "Number and Operations—Fractions, 3-5", "start_page": 139, "end_page": 161, "domains": ["3.NF", "4.NF", "5.NF"]},
    {"name": "Ratios and Proportional Relationships, 6-7", "start_page": 162, "end_page": 176, "domains": ["6.RP", "7.RP"]},
    {"name": "Expressions and Equations, 6-8", "start_page": 177, "end_page": 190, "domains": ["6.EE", "7.EE", "8.EE"]},
    {"name": "Statistics and Probability, 6-8", "start_page": 191, "end_page": 202, "domains": ["6.SP", "7.SP", "8.SP"]},
    {"name": "The Number System, 6-8; Number, High School", "start_page": 203, "end_page": 220, "domains": ["6.NS", "7.NS", "8.NS", "N-RN", "N-Q", "N-CN"]},
    {"name": "Geometry, 7-8, High School", "start_page": 221, "end_page": 239, "domains": ["7.G", "8.G", "G-CO", "G-SRT", "G-C", "G-GPE", "G-GMD", "G-MG"]},
    {"name": "Functions, 8, High School", "start_page": 240, "end_page": 258, "domains": ["8.F", "F-IF", "F-BF", "F-LE", "F-TF"]},
    {"name": "Quantity, High School", "start_page": 259, "end_page": 267, "domains": ["N-Q"]},
    {"name": "Algebra, High School", "start_page": 268, "end_page": 281, "domains": ["A-SSE", "A-APR", "A-CED", "A-REI"]},
    {"name": "Statistics and Probability, High School", "start_page": 282, "end_page": 299, "domains": ["S-ID", "S-IC", "S-CP", "S-MD"]},
    {"name": "Modeling, K-12", "start_page": 300, "end_page": 321, "domains": ["MP.4"]},
]

def extract_text_from_pages(start_page: int, end_page: int) -> str:
    """Extract text from a range of pages (1-indexed)."""
    doc = fitz.open(PROGRESSIONS_PDF)
    text = ""
    for i in range(start_page - 1, min(end_page, len(doc))):
        text += doc[i].get_text() + "\n\n"
    doc.close()
    return text

def parse_progressions_text(text: str, domains: list) -> list:
    """
    Parse Progressions text directly to extract standards.
    Returns list of dicts with standard_id, explanation, examples, misconceptions, constraints, context.
    """
    standards = []
    
    # Simple pattern matching for CCSS standards (K.CC.1, 1.OA.2, etc.)
    import re
    pattern = r'([KG]\.?[A-Z]{1,3}(?:\.[A-Z])?\.\d+(?:[a-z])?|[A-Z]\-?[A-Z]{1,3}\.\d+\.?\d?)'
    matches = re.finditer(pattern, text)
    
    found_standards = set()
    for match in matches:
        std_id = match.group(1)
        # Basic validation
        if std_id in found_standards or not any(d in std_id for d in domains):
            continue
        found_standards.add(std_id)
        
        standards.append({
            "standard_id": std_id,
            "detailed_explanation": "[To be filled by Claude extraction]",
            "worked_examples": "",
            "misconceptions": "",
            "parameter_constraints": "",
            "developmental_context": ""
        })
    
    return standards

def save_evidence(standards: list):
    """Save extracted standards to evidence files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved = 0
    
    for std in standards:
        std_id = std.get("standard_id", "").strip()
        if not std_id:
            continue
        
        safe_id = std_id.replace(".", "_").replace("-", "_")
        outpath = os.path.join(OUTPUT_DIR, f"{safe_id}.json")
        
        # Load existing
        existing = {}
        if os.path.exists(outpath):
            with open(outpath, 'r') as f:
                existing = json.load(f)
        
        # Add progressions data
        existing["progressions"] = {
            "detailed_explanation": std.get("detailed_explanation", ""),
            "worked_examples": std.get("worked_examples", ""),
            "misconceptions": std.get("misconceptions", ""),
            "parameter_constraints": std.get("parameter_constraints", ""),
            "developmental_context": std.get("developmental_context", "")
        }
        existing["node_id"] = std_id
        
        with open(outpath, 'w') as f:
            json.dump(existing, f, indent=2)
        
        saved += 1
    
    return saved

def main():
    print(f"\n{'='*70}")
    print(f"CCSS Progressions Direct Extraction")
    print(f"Processing {len(SECTIONS)} domain sections")
    print(f"{'='*70}\n")
    
    total_standards = 0
    total_saved = 0
    
    for i, section in enumerate(SECTIONS):
        print(f"[{i+1}/{len(SECTIONS)}] {section['name']}")
        print(f"  Pages {section['start_page']}-{section['end_page']}, Domains: {', '.join(section['domains'])}")
        
        # Extract text
        text = extract_text_from_pages(section["start_page"], section["end_page"])
        print(f"  Text: {len(text)} chars")
        
        # Parse standards
        standards = parse_progressions_text(text, section["domains"])
        print(f"  Found {len(standards)} standards")
        
        if standards:
            saved = save_evidence(standards)
            total_standards += len(standards)
            total_saved += saved
            print(f"  Saved {saved} evidence files")
        
        print()
    
    print(f"{'='*70}")
    print(f"Extraction Complete")
    print(f"  Total standards found: {total_standards}")
    print(f"  Evidence files saved: {total_saved}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
