# trust-indicators
This is the repository for the AMT project "Personalized Media Streams Through Trust Indicators"

## Configuration

To run the service, you need a Google Gemini API key and a Google Fact Checking API key.

1. Create two API keys from [Google Console](https://console.cloud.google.com/apis/dashboard).
   1. Create one for: Generative Language API
   2. Create one for: Fact Check Tools API

This will possibly be the same key for both APIs.

## Run the application with Docker

1. set your two API keys in docker-compose.yml
2. run `docker compose up` in your terminal from the root of the project.
3. go to http://localhost:5173