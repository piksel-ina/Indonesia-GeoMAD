FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.0

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

ENV GDAL_DATA=/usr/share/gdal \
    PROJ_DATA=/usr/local/share/proj \
    PROJ_LIB=/usr/local/share/proj

COPY docker/distributed.yaml /etc/dask/distributed.yaml

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y \
      build-essential \
      git \
      python3-venv \
      python3-dev \
      libpq-dev \
      postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv ${VIRTUAL_ENV}
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY pyproject.toml /app/
COPY uv.lock /app/uv.lock

RUN uv sync --active --no-dev --frozen

ENV DATACUBE_CONFIG_PATH=/etc/datacube/datacube.conf

COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odc-stats", "--help"]
