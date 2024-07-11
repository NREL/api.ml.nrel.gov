FROM condaforge/mambaforge
# update to fix some vulnerabilities
RUN apt-get update && apt-get -y upgrade

COPY etc/environment.yml /tmp/environment.yml
WORKDIR /tmp
RUN mamba env update -f environment.yml && \
    rm -rf /tmp/* && conda clean --all --yes

RUN mkdir -p /deploy/app
COPY src /deploy/app
COPY etc/run_tests.sh /deploy/app
RUN chmod +x /deploy/app/run_tests.sh

# cleanup after the update and upgrade
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean
    

WORKDIR /deploy/app
ENV PYTHONPATH="${PYTHONPATH}:/deploy/app"
ENV PORT=8889

CMD gunicorn --worker-tmp-dir /dev/shm --bind 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker --log-level debug wsgi:app
