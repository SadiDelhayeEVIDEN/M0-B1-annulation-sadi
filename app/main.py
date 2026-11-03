"""API de prédiction d'annulation — Escale Atlantique (mission FastIA)."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

from app.schemas import Booking, PredictionResponse

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", ROOT_DIR / "model" / "cancellation_model.joblib"))

# Objets partagés par toutes les requêtes (ici : le modèle)
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Exécuté UNE fois au démarrage : on charge le modèle en mémoire
    state["model"] = joblib.load(MODEL_PATH)
    yield
    # Exécuté à l'arrêt du serveur
    state.clear()


app = FastAPI(
    title="Escale Atlantique — Prédiction d'annulation",
    description="Estime la probabilité qu'une réservation soit annulée.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    """Le service est-il en vie, et le modèle chargé ?"""
    return {"status": "ok", "model_loaded": "model" in state}


@app.post("/predict", response_model=PredictionResponse)
def predict(booking: Booking) -> PredictionResponse:
    """Prédit l'annulation d'une réservation."""
    model = state.get("model")
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    # Une ligne, avec les colonnes dans l'ordre vu à l'entraînement
    X = pd.DataFrame([booking.model_dump()], columns=model.feature_names_in_)

    annulation = bool(model.predict(X)[0])
    probabilite = float(model.predict_proba(X)[0, 1])  # colonne 1 = classe « annulée »
    return PredictionResponse(annulation=annulation, probabilite_annulation=probabilite)
