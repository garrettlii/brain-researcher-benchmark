FROM ubuntu:24.04 AS dependencies
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# Versions are the ones that ran the oracle (step0/outputs/pip_freeze.txt); the mne
# dependency closure is pinned too so the resolver cannot drift.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates python3 python3-venv python3-pip && \
    python3 -m pip install --break-system-packages --no-cache-dir \
      numpy==2.5.3 \
      scipy==1.18.1 \
      scikit-learn==1.9.1 \
      joblib==1.6.0 \
      threadpoolctl==3.7.0 \
      pandas==3.0.6 \
      python-dateutil==2.9.0.post0 \
      six==1.17.0 \
      PyWavelets==1.10.0 \
      mne==1.13.2 \
      matplotlib==3.11.2 \
      contourpy==1.4.0 \
      cycler==0.12.1 \
      fonttools==4.66.1 \
      kiwisolver==1.5.1 \
      pillow==12.3.0 \
      pyparsing==3.3.3 \
      decorator==5.3.1 \
      Jinja2==3.1.6 \
      MarkupSafe==3.0.4 \
      lazy-loader==0.6 \
      packaging==26.3 \
      pooch==1.9.0 \
      platformdirs==4.12.4 \
      requests==2.34.2 \
      certifi==2026.7.22 \
      charset-normalizer==3.5.2 \
      idna==3.20 \
      urllib3==2.8.0 \
      tqdm==4.70.1 \
      pytest==9.1.1 \
      pytest-json-ctrf==0.3.5 \
      iniconfig==2.3.1 \
      pluggy==1.6.0 \
      Pygments==2.21.0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# The 31 recordings are downloaded and sha256-checked once, at build time; the task runs offline.
FROM dependencies AS source
COPY stage_data.py source_manifest.json /opt/source/
RUN timeout --kill-after=10s 1800s python3 -I -B /opt/source/stage_data.py \
      --manifest /opt/source/source_manifest.json --destination /app/data/ds002778

FROM dependencies AS runtime
COPY --from=source /app/data/ds002778 /app/data/ds002778
COPY source_manifest.json output_schema.json SOURCE_NOTICE.md /app/
WORKDIR /app
RUN mkdir -p /app/output
