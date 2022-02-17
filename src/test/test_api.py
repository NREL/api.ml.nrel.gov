from urllib.parse import quote

from fastapi.testclient import TestClient
from ysi_api import app

fastapi_client = TestClient(app)


def test_path_api():
    data = fastapi_client.get("/predict/CCO").json()
    assert data["status"] == "ok"

    data = fastapi_client.get("/predict/CB").json()
    assert data["outlier"] is True

    data = fastapi_client.get("/predict/X").json()
    assert data['detail'] == "Invalid smiles: X"


def test_query_api():
    smiles = "C/C=C\\CCCC"
    data = fastapi_client.get(f"/predict?smiles={quote(smiles)}").json()
    assert data["status"] == "ok"

    data = fastapi_client.get(f"/predict?smiles={smiles}").json()
    assert data["status"] == "ok"
