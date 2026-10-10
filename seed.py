"""Create tables and print course counts. Running repeatedly is safe."""
from app import app, db, COURSES
with app.app_context():
    db.create_all()
    print(f"LearnAI database is ready. {len(COURSES)} starter courses are available.")
