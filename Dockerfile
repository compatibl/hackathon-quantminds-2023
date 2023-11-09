FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY ./hackathon/requirements.lock /app/requirements.lock

RUN pip install --no-cache-dir --upgrade -r /app/requirements.lock

COPY . /app

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

ENTRYPOINT ["/app/entrypoint.sh"]
