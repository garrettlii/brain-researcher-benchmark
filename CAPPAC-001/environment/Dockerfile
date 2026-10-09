FROM ubuntu:24.04 AS dependencies
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# Versions are the ones that ran the oracle (step0/outputs/pip_freeze.txt), with pandas'
# dependency closure pinned so the resolver cannot drift; pytest is pinned here too so the
# verifier runs offline.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates python3 python3-venv python3-pip && \
    python3 -m pip install --break-system-packages --no-cache-dir \
      numpy==2.5.3 \
      scipy==1.18.1 \
      pandas==3.0.6 \
      python-dateutil==2.9.0.post0 \
      six==1.17.0 \
      pytest==9.1.1 \
      pytest-json-ctrf==0.3.5 \
      iniconfig==2.3.1 \
      packaging==26.3 \
      pluggy==1.6.0 \
      Pygments==2.21.0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# The 32 CAP Sleep Database files (3.8 GB) are downloaded and sha256-checked once, at build time;
# the task runs offline.
FROM dependencies AS source
COPY stage_data.py source_manifest.json /opt/source/
RUN timeout --kill-after=10s 3300s python3 -I -B /opt/source/stage_data.py \
      --manifest /opt/source/source_manifest.json --destination /app/data/capslpdb

FROM dependencies AS runtime
COPY --from=source /app/data/capslpdb /app/data/capslpdb
COPY source_manifest.json SOURCE_NOTICE.md /app/
RUN chmod -R a-w /app/data/capslpdb && mkdir -p /app/output
WORKDIR /app
