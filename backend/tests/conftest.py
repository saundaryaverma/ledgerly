import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite://")  # tests never touch a real database file

from app import db, main  # noqa: E402

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample_data", "transactions.csv")


@pytest.fixture
def client(tmp_path):
    url = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    engine = db.make_engine(url)
    db.Base.metadata.drop_all(engine)
    db.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    main.app.dependency_overrides[db.get_session] = override
    main._ASK, main._REWRITE = None, None
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
    engine.dispose()


def upload(client, text, name="bank.csv"):
    return client.post("/api/import", files={"file": (name, text.encode(), "text/csv")})


@pytest.fixture
def loaded(client):
    with open(SAMPLE) as f:
        r = upload(client, f.read())
    assert r.status_code == 200, r.text
    return client
