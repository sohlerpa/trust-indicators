# trust-indicators
This is the repository for the AMT project "Personalized Media Streams Through Trust Indicators"

## Configuration

To run the service, you need a Google Gemini API key.

1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Create a file named `.env` in the project root.
3. Add your key to the file:
   ```env
   GEMINI_API_KEY=your_api_key_here
   
## Run the application

To run the application, you have to start both the backend and the frontend separately:

1. start the docker `docker compose up -d`
2. start the backend `cd backend` & `pip install -e .` & `python run.py`
3. start the frontend `cd frontend` & `npm install` & `npm run dev`
   
## Architecture

It is divided into a frontend and backend project

### Source Funding
1. start the service
2. Issue queries via HTTP:
- either: GET localhost:8000/api/domain/zeit.de/owners (or any other domain)
- or: POST localhost:8000/api/feed/diversity with body ```["welt.de", "bild.de", "zeit.de", "spiegel.de"]``` (no json object, just plain array)

### Tone & Type Classifier
You can call the module like in the example:

```python
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

### Author Expertise Classifier

You can call the module like in the example:

```python
from backend.src.modules.author_expertise.author_expertise_classifier import assess_author_expertise

text = "insert article text here"
author = "Feix Kiefer"
url = "https://www.tagesspiegel.de/politik/riester-rente-20-so-soll-die-private-altersvorsorge-kunftig-funktionieren-15030828.html"

result = assess_author_expertise(text, author, url)
print(result)
```

Expected output:
 ```
author='Felix Kiefer'
article_url='https://www.tagesspiegel.de/politik/riester-rente-20-so-soll-die-private-altersvorsorge-kunftig-funktionieren-15030828.html'
publisher_domain='tagesspiegel.de'
field='Financial Policy'
label='uncertain'
confidence=0.8
explanation="Despite the article reading like it was written by a domain expert, with high accuracy and specificity in financial policy, external credentialing information for Felix Kiefer is uncertain. Therefore, a definitive 'field_expert' label cannot be assigned."
```