# Escale Atlantique — API de prédiction d'annulation

Escale Atlantique gère deux hôtels : un hôtel de centre-ville et un complexe hôtelier. Environ une réservation sur trois est annulée.

Ce service est une petite API web. Vous lui envoyez une réservation, et il vous indique si celle-ci est susceptible d'être annulée, avec une probabilité comprise entre 0 et 1. La prédiction est générée par un modèle d'apprentissage automatique pré-entraîné, situé dans le répertoire `model/`.

## Ce dont vous avez besoin avant de commencer

- **Pour lancer en local** : Python 3.11 ou 3.12.
- **Pour lancer avec Docker** : Docker (Docker Desktop sous Windows et macOS).

Toutes les commandes se lancent depuis la racine du projet.

## 1. Installation (en local)

```bash
# Créer un environnement virtuel
python -m venv .venv

# L'activer
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# Installer les dépendances
pip install -r requirements.txt
```

## 2. Lancer le service

```bash
uvicorn app.main:app --reload
```

Le service démarre sur le port 8000. Pour vérifier qu'il tourne :

- http://localhost:8000/health doit afficher `{"status":"ok","model_loaded":true}`
- http://localhost:8000/docs ouvre une page de documentation où l'on peut tester l'API directement dans le navigateur (bouton **Try it out**).

`--reload` relance le service à chaque modification du code. C'est pratique pour développer, inutile en production.

Pour arrêter le service : `Ctrl + C`.

## 3. Lancer le service avec Docker

Docker évite d'installer Python : tout ce dont le service a besoin est dans l'image.

```bash
# Construire l'image (à refaire après chaque modification du code)
docker build -t fastia-annulation:dev .

# Lancer le service
docker run --rm -p 8000:8000 fastia-annulation:dev
```

Puis, depuis un autre terminal :

```bash
curl http://localhost:8000/health
```

## 4. Lancer les tests

Les tests n'ont pas besoin que le service soit lancé.
Avec l'environnement virtuel activé :

```bash
pytest -v
```

Ils vérifient que `/health` répond, qu'une réservation valide reçoit une prédiction correcte, et qu'une réservation invalide est refusée.

## 5. Exemple d'appel à `/predict`

Le fichier `data/exemple_reservation.json` contient une réservation prête à l'emploi.

**macOS / Linux / Git Bash :**

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  --data @data/exemple_reservation.json
```

**Windows PowerShell :**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict `
  -ContentType "application/json" `
  -InFile data/exemple_reservation.json
```

**Réponse :**

```json
{"annulation": false, "probabilite_annulation": 0.000265}
```

- `annulation` : `true` si le modèle pense que la réservation sera annulée (probabilité de 0,5 ou plus).
- `probabilite_annulation` : la probabilité d'annulation, entre 0 et 1.

### Les champs à envoyer

Les 15 champs sont **obligatoires**. Si un champ manque ou a une valeur interdite, l'API répond avec le code **422** et un message qui indique le champ en cause.

| Champ | Valeurs acceptées |
|---|---|
| `hotel` | `City Hotel`, `Resort Hotel` |
| `arrival_date_month` | le mois en anglais : `January` … `December` |
| `market_segment` | `Aviation`, `Complementary`, `Corporate`, `Direct`, `Groups`, `Offline TA/TO`, `Online TA`, `Undefined` |
| `deposit_type` | `No Deposit`, `Non Refund`, `Refundable` |
| `customer_type` | `Contract`, `Group`, `Transient`, `Transient-Party` |
| `country` | code pays en majuscules, ex. `FRA`, `PRT`, `GBR` |
| `lead_time` | jours entre la réservation et l'arrivée : 0 à 1000 |
| `stays_in_weekend_nights` | 0 à 30 |
| `stays_in_week_nights` | 0 à 75 |
| `adults` | 0 à 10 |
| `children` | 0 à 10 (au moins une personne au total, adultes + enfants) |
| `adr` | prix moyen d'une nuit, en euros : 0 à 1000 |
| `previous_cancellations` | 0 à 50 |
| `total_of_special_requests` | 0 à 10 |
| `required_car_parking_spaces` | 0 à 10 |

## Les logs

Chaque appel à `/predict` est enregistré dans `logs/api.log` : la réservation reçue, la prédiction et le temps de calcul. Un nouveau fichier est créé tous les 5 Mo. Les anciens sont compressés en `.zip`, puis supprimés au bout de 7 jours.

## Réglages (variables d'environnement)

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `MODEL_PATH` | fichier du modèle à charger | `model/cancellation_model.joblib` |
| `LOG_PATH` | fichier de logs | `logs/api.log` |

## Organisation du projet

```
app/
  main.py          # l'API : démarrage, /health, /predict, logs
  schemas.py       # format des réservations acceptées et des réponses
model/
  cancellation_model.joblib   # modèle entraîné (ne pas modifier)
  model_info.json             # fiche du modèle : version, colonnes, scores
  train_baseline.py           # script d'entraînement, pour information
data/
  hotel_bookings_sample.csv   # 1 000 réservations réelles, pour exemples et tests
  exemple_reservation.json    # exemple de requête pour /predict
tests/                        # tests automatiques (pytest)
Dockerfile, .dockerignore     # construction de l'image Docker
pytest.ini                    # configuration de pytest
requirements.txt              # bibliothèques et versions
```

## Données

Extrait de *Hotel Booking Demand* — N. Antonio, A. de Almeida, L. Nunes (2019), *Data in Brief* 22, 41-49. Licence CC BY 4.0.
