# trust-indicators
This is the repository for the AMT project "Personalized Media Streams Through Trust Indicators"

## Configuration

To run the service, you need a Google Gemini API key.

1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Create a file named `.env` in the project root.
3. Add your key to the file:
   ```env
   GEMINI_API_KEY=your_api_key_here
   
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

### Tone & Type Classifier
You can call the module like in the example:

```
from backend.src.modules.tone.tone_classifier import classify_tone

sample = "Breaking: City officials unveil a plan to redesign downtown streets, aiming to cut traffic by 30% within two years, according to documents released Tuesday."
result = classify_tone(sample)
print(result.to_json())
```

Expected output:
````json
{
   "content_type":"news",
   "tone":"neutral",
   "confidence":0.95,
   "rationale":"The text is a straightforward report of a factual event (city officials unveiling a plan) with specific details (30% traffic reduction, two years, documents released Tuesday). It does not express personal viewpoints, speculation, or emotional language, making 'news' and 'neutral' the most appropriate classifications."
}
````
