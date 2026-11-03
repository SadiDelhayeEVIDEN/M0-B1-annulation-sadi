import json
from pathlib import Path

import pytest

EXEMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "exemple_reservation.json"


@pytest.fixture
def reservation():
    return json.loads(EXEMPLE_PATH.read_text(encoding="utf-8"))


def test_predict_valide(client, reservation):
    response = client.post("/predict", json=reservation)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["annulation"], bool)
    assert 0 <= body["probabilite_annulation"] <= 1


def test_predict_hotel_inconnu(client, reservation):
    reservation["hotel"] = "Motel"
    assert client.post("/predict", json=reservation).status_code == 422


@pytest.mark.parametrize("hotel", ["City Hotel", "Resort Hotel"])
def test_predict_types_hotel(client, reservation, hotel):
    reservation["hotel"] = hotel
    assert client.post("/predict", json=reservation).status_code == 200
