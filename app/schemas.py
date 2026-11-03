"""Schémas Pydantic : format des entrées et des sorties de l'API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Valeurs connues du modèle (catégories apprises à l'entraînement)
Hotel = Literal["City Hotel", "Resort Hotel"]
Month = Literal[
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MarketSegment = Literal[
    "Aviation", "Complementary", "Corporate", "Direct",
    "Groups", "Offline TA/TO", "Online TA", "Undefined",
]
DepositType = Literal["No Deposit", "Non Refund", "Refundable"]
CustomerType = Literal["Contract", "Group", "Transient", "Transient-Party"]

EXEMPLE = {
    "hotel": "Resort Hotel",
    "lead_time": 164,
    "arrival_date_month": "November",
    "stays_in_weekend_nights": 2,
    "stays_in_week_nights": 5,
    "adults": 2,
    "children": 0,
    "market_segment": "Online TA",
    "deposit_type": "No Deposit",
    "customer_type": "Transient",
    "country": "FRA",
    "adr": 61.2,
    "previous_cancellations": 0,
    "total_of_special_requests": 0,
    "required_car_parking_spaces": 1,
}


class Booking(BaseModel):
    """Une réservation, telle que saisie dans le logiciel de gestion hôtelière.

    Les noms de champs sont ceux du jeu de données d'entraînement :
    le modèle attend exactement ces colonnes. Tous les champs sont obligatoires.
    Les bornes laissent de la marge au-dessus des valeurs observées dans les données.
    """

    model_config = ConfigDict(json_schema_extra={"examples": [EXEMPLE]})

    hotel: Hotel
    lead_time: int = Field(ge=0, le=1000, description="Jours entre la réservation et l'arrivée")
    arrival_date_month: Month
    stays_in_weekend_nights: int = Field(ge=0, le=30)
    stays_in_week_nights: int = Field(ge=0, le=75)
    adults: int = Field(ge=0, le=10)
    children: int = Field(ge=0, le=10)
    market_segment: MarketSegment
    deposit_type: DepositType
    customer_type: CustomerType
    # Code pays ISO en majuscules : 3 lettres en général, mais « CN » existe dans les données
    country: str = Field(pattern=r"^[A-Z]{2,3}$", description="Code pays ISO, ex. FRA")
    adr: float = Field(ge=0, le=1000, description="Prix moyen par nuit, en euros")
    previous_cancellations: int = Field(ge=0, le=50)
    total_of_special_requests: int = Field(ge=0, le=10)
    required_car_parking_spaces: int = Field(ge=0, le=10)

    @model_validator(mode="after")
    def au_moins_une_personne(self) -> "Booking":
        if self.adults + self.children == 0:
            raise ValueError("La réservation doit compter au moins un adulte ou un enfant")
        return self


class PredictionResponse(BaseModel):
    """Réponse de /predict."""

    annulation: bool
    probabilite_annulation: float = Field(ge=0, le=1)
