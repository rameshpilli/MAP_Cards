FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

RUN python -m map_cards.seed

CMD ["uvicorn", "map_cards.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
