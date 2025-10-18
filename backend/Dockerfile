FROM python:3.13

WORKDIR /app
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/pip pip install .

WORKDIR /app/app
COPY app .

CMD [ "python", "main.py" ]