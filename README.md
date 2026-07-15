# Skycast — Django Weather + AI Advisor

A portfolio-ready Django app that integrates a **third-party weather API** (OpenWeatherMap) and an **AI advice endpoint** (OpenAI when configured, rule-based advisor otherwise). Shows how models don’t ship themselves — you wire APIs, cache, logging, and a reliable UX.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-5.x-green)
![OpenWeather](https://img.shields.io/badge/API-OpenWeatherMap-2f86b8)
![AI](https://img.shields.io/badge/AI-OpenAI%20optional-e8a838)

## Features

- City weather lookup via OpenWeatherMap (current + 5-day snapshot)
- JSON APIs for clients: `/api/weather/` and `/api/advice/`
- Optional OpenAI briefing; automatic **rules-based fallback** without a key
- Demo weather data when no OpenWeather key is set (portfolio still runs)
- Response caching + lookup / advice audit models
- Clean Skycast UI for screenshots and demos

## Quick start

```bash
git clone https://github.com/TahaGabu/django-weather-api.git
cd django-weather-api

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux

python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and search a city (demo mode works immediately).

### Live OpenWeather

1. Create a free key at [openweathermap.org/api](https://openweathermap.org/api)
2. Put it in `.env`:

```env
OPENWEATHER_API_KEY=your_key_here
```

3. Restart the server. New keys can take a few minutes to activate.

### Optional OpenAI advisor

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Without this key, `/api/advice/` still returns high-quality rule-based tips from the weather payload.

## API examples

```bash
curl "http://127.0.0.1:8000/api/weather/?city=London"
curl "http://127.0.0.1:8000/api/advice/?city=Mumbai"
curl -X POST http://127.0.0.1:8000/api/advice/ ^
  -H "Content-Type: application/json" ^
  -d "{\"city\":\"Tokyo\"}"
```

## Project structure

```
├── config/           # Settings, URLs, WSGI
├── weather/          # Models, OpenWeather + AI services, views
├── static/           # CSS / JS
├── templates/        # Skycast UI
├── manage.py
├── requirements.txt
└── .env.example
```

## Stack

| Layer       | Choice                                      |
|-------------|---------------------------------------------|
| Backend     | Django 5                                    |
| Weather API | OpenWeatherMap Current + Forecast           |
| AI advice   | OpenAI Chat Completions (optional)          |
| HTTP client | `requests`                                  |
| Cache       | Django local memory cache                   |
| Static      | WhiteNoise                                  |

## Why this belongs on a portfolio

“Connect this AI model to our product” is a common 2026 brief. Skycast shows the integration pattern: external API → normalize data → optional AI layer → fallback path → JSON API → UI — the production glue hireable developers actually ship.

## License

MIT — use it freely in interviews and demos.
