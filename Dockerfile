FROM continuumio/miniconda3

COPY ysipred/environment.yml /tmp/environment.yml
WORKDIR /tmp
RUN apt-get update && \
    apt-get install -y --no-install-recommends libxrender1 && \
    conda env update -f environment.yml

RUN mkdir -p /deploy/app
COPY ysipred /deploy/app

WORKDIR /deploy/app

ENTRYPOINT ["/bin/bash", "-c"]
CMD gunicorn --bind 0.0.0.0:$PORT main:app
