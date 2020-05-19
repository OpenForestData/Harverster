FROM python:3.8-slim-buster

EXPOSE 8000
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y \
    git

# Copy data
ADD . /app

RUN  pip install -r requirements.txt

RUN chmod +x /app/docker/entrypoint.sh
RUN chmod +x /app/docker/wait_for.sh
RUN chmod -R 755 /app

CMD [ "/app/docker/entrypoint.sh" ]
