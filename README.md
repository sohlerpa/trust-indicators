# trust-indicators
This is the repository for the AMT project "Personalized Media Streams Through Trust Indicators"

## Architecture

It is divided into a frontend and backend project

### Source Funding
1. start the database with ```docker compose up -d```
2. Go to the src
```cd backend/src```
3. Start the service
```uvicorn app.main:app --reload```
4. Issue queries via HTTP:
- either: GET localhost:8000/domain/zeit.de/owners (or any other domain)
- or: POST localhost:8000/feed/diversity with body ```["welt.de", "bild.de", "zeit.de", "spiegel.de"]``` (no json object, just plain array)