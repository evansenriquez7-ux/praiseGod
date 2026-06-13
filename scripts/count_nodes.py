import sys
import os

# Add parent directory to path so we can import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app.models import SkillNode

def main():
    db = SessionLocal()
    nodes = db.query(SkillNode).all()
    print(f"Total nodes in database: {len(nodes)}")
    
    grade_counts = {}
    for node in nodes:
        grade = node.grade_level or "Unknown"
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
    print("\nGrade level distribution:")
    for grade, count in sorted(grade_counts.items(), key=lambda x: str(x[0])):
        print(f"Grade {grade}: {count} nodes")
        
    db.close()

if __name__ == "__main__":
    main()
