ARG PYTHON_IMAGE=python:3.12.11-slim-bookworm
FROM scratch AS source
COPY . /opt/aurora

FROM ${PYTHON_IMAGE} AS cpu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/aurora \
    AURORA_WORKFLOW_VENV=/usr/local \
    AURORA_WORKFLOW_CONFIG=/config/workflow.json \
    CDSAPI_RC=/config/ads.credentials
WORKDIR /opt/aurora
COPY requirements/workflow-light.txt requirements/workflow-data.txt /tmp/requirements/
RUN python -m pip install --no-cache-dir -r /tmp/requirements/workflow-data.txt \
    && groupadd --gid 10001 aurora \
    && useradd --uid 10001 --gid aurora --create-home --shell /usr/sbin/nologin aurora
COPY --from=source /opt/aurora /opt/aurora
USER aurora
ENTRYPOINT ["/opt/aurora/bin/aurora-mcp"]

FROM nvcr.io/nvidia/pytorch:25.08-py3 AS cuda
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/aurora \
    AURORA_WORKFLOW_VENV=/usr/local \
    AURORA_WORKFLOW_CONFIG=/config/workflow.json \
    CDSAPI_RC=/config/ads.credentials
WORKDIR /opt/aurora
COPY requirements/workflow-light.txt requirements/workflow-data.txt /tmp/requirements/
RUN python -m pip install --no-cache-dir -r /tmp/requirements/workflow-data.txt \
    && groupadd --gid 10001 aurora \
    && useradd --uid 10001 --gid aurora --create-home --shell /usr/sbin/nologin aurora \
    && python -c 'import sys, torch; assert (3, 12) <= sys.version_info[:2] <= (3, 14); print("Python", sys.version.split()[0], "PyTorch", torch.__version__, "CUDA", torch.version.cuda)'
COPY --from=source /opt/aurora /opt/aurora
USER aurora
ENTRYPOINT ["/opt/aurora/bin/aurora-mcp"]
