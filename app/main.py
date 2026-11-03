"""API de prédiction d'annulation — Escale Atlantique (mission FastIA)."""

import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from loguru import logger

from app.schemas import Booking, PredictionResponse

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = Path(os.getenv("MODEL_PATH", ROOT_DIR / "model" / "cancellation_model.joblib"))
LOG_PATH = Path(os.getenv("LOG_PATH", ROOT_DIR / "logs" / "api.log"))
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"

# Objets partagés par toutes les requêtes (ici : le modèle)
state: dict = {}


def configure_logging() -> None:
    """Logs dans la console et dans logs/api.log (rotation, rétention, compression)."""
    logger.remove()
    logger.add(sys.stderr, level="INFO", format=LOG_FORMAT)
    logger.add(
        LOG_PATH,
        level="INFO",
        format=LOG_FORMAT,
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Exécuté UNE fois au démarrage : logs, puis chargement du modèle en mémoire
    configure_logging()
    state["model"] = joblib.load(MODEL_PATH)
    logger.info("Modèle chargé : {}", MODEL_PATH)
    yield
    # Exécuté à l'arrêt du serveur
    logger.info("Arrêt du service")
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

    start = time.perf_counter()

    # Une ligne, avec les colonnes dans l'ordre vu à l'entraînement
    X = pd.DataFrame([booking.model_dump()], columns=model.feature_names_in_)

    annulation = bool(model.predict(X)[0])
    probabilite = float(model.predict_proba(X)[0, 1])  # colonne 1 = classe « annulée »

    duree_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "predict | entree={} | annulation={} | probabilite={:.3f} | duree={:.1f} ms",
        booking.model_dump_json(),
        annulation,
        probabilite,
        duree_ms,
    )
    return PredictionResponse(annulation=annulation, probabilite_annulation=probabilite)
