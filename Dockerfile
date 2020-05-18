FROM python:3.8-alpine

ENV PYTHONUNBUFFERED 1

# Set main folder
WORKDIR /app


# Copy requirements and install pip dependencies
COPY ./requirements.txt ./
RUN  pip install -r requirements.txt

# Copy data
ADD . /app

RUN chmod +x /app/docker/entrypoint.sh
RUN chmod -R 755 /app

CMD [ "/app/docker/entrypoint.sh" ]
