# shared/init_db.py
from shared.db import engine
from shared.models import Base


def init_db():
    print("DATABASE_URL =", engine.url)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized")
