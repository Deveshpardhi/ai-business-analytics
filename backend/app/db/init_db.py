from app.db.base import Base
from app.db.database import engine

from app.models.dataset import Dataset, DatasetVersion
from app.models.analysis import AnalysisRun


def init_db():
    """Legacy local/test schema helper; production schema changes use Alembic."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")
