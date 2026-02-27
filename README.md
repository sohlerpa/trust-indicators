# Personalized Media Streams Through Trust Indicators
This is the repository for the AMT project "Personalized Media Streams Through Trust Indicators" at TU Berlin.

## Requirements

- Docker needs to be installed and running. [click here to get Docker](https://docs.docker.com/get-started/get-docker/)
- A Google Gemini API key and a Google Fact Checking API key are needed.
  - If you haven't been provided with those, create two API keys from [Google Console](https://console.cloud.google.com/apis/dashboard).
     1. Create one for: Generative Language API
     2. Create one for: Fact Check Tools API

## Run the application with Docker

1. Set your two API keys in `docker-compose.yml`.
2. Run `docker compose up` in your terminal from the root of the project.
3. Go to http://localhost:5173