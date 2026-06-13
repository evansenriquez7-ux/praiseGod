from backend.app.database import engine, Base
from backend.app.models import ParentAccount, StudentProfile, SkillNode, SkillEdge, MasteryState, TelemetrySession, Attempt, SpacedRepetition, QuestionFlag, CompetencyConfiguration

def main():
    print("Creating all tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    main()
