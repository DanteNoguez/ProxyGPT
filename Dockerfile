FROM python:3.9-bullseye

RUN apt-get -y update
RUN apt-get -y upgrade

WORKDIR /code
ADD .env /code/.env
ADD ./pyproject.toml /code/pyproject.toml
ADD ./poetry.lock /code/poetry.lock
RUN pip install --no-cache-dir --upgrade poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-ansi -vvv

ADD main.py /code/main.py
ADD config.py /code/config.py
ADD redis_db.py /code/redis_db.py
ADD models.py /code/models.py

ENTRYPOINT ["gunicorn"]
CMD ["-k", "uvicorn.workers.UvicornWorker", "main:app", "-w", "1", "--bind", "0.0.0.0:8081"]