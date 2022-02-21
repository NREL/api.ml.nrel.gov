import json
import os
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient
from ysi_api import app

dir_path = os.path.dirname(os.path.realpath(__file__))
fastapi_client = TestClient(app)


def test_path_api():
    data = fastapi_client.get("/predict/CCO").json()
    assert data["status"] == "ok"

    data = fastapi_client.get("/predict/CB").json()
    assert data["outlier"] is True

    data = fastapi_client.get("/predict/X").json()
    assert data["detail"] == "Invalid smiles: X"


def test_query_api():
    smiles = "C/C=C\\CCCC"
    data = fastapi_client.get(f"/predict?smiles={quote(smiles)}").json()
    assert data["status"] == "ok"

    data = fastapi_client.get(f"/predict?smiles={smiles}").json()
    assert data["status"] == "ok"


def test_result():
    data = fastapi_client.get(r"/result/C/C(=C\c1ccccc1)c1ccccc1").json()
    assert "svg" in data["mol_svg"]
    assert (
        data["named_smiles"] == "C/C(=C\\c1ccccc1)c1ccccc1 (trans 1,2-diphenylpropene)"
    )
    assert data["status"] == "ok"


def test_frag():
    frag = "[H]-[C](-[H])(-[C])-[C] | (Ring)"
    data = fastapi_client.get(f"/frag/{quote(frag)}").json()
    assert "svg" in data["frag_svg"]
    assert data["status"] == "ok"
