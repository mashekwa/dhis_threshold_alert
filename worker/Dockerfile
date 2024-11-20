FROM python:3.9-slim

WORKDIR /app

# install supervisord
RUN apt-get update && apt-get install -y supervisor libpq-dev gcc
RUN pip install --upgrade pip
# copy requirements and install (so that changes to files do not mean rebuild cannot be cached)
COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# copy all files into the container
COPY . .

# needs to be set else Celery gives an error (because docker runs commands inside container as root)
RUN useradd -m celery_user && \
    chown -R celery_user:celery_user /app

USER celery_user


# run supervisord
CMD ["/usr/bin/supervisord"]
