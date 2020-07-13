FROM python:3.8-alpine

EXPOSE 8000
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add --no-cache curl postgresql-libs gcc musl-dev postgresql-dev python3-dev git

COPY ./requirements.txt /app
RUN  pip install -r requirements.txt

ADD . /app

RUN chmod +x /app/docker/entrypoint.sh
RUN chmod +x /app/docker/wait_for.sh
RUN chmod -R 755 /app

CMD /bin/sh -c '/app/docker/wait-for harvester_db:5432 -t 20 -- /bin/sh /app/docker/entrypoint.sh'