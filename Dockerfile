# syntax=docker/dockerfile:1

# === Base image with Python and user setup ===
FROM python:3.13-slim AS base
ARG USERNAME=pyuser
ARG GROUPNAME=pyuser
ARG UID=1000
ARG GID=1000

WORKDIR /code
RUN pip install -U pip && pip install uv

RUN groupadd -g ${GID} ${GROUPNAME} && \
    useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME}
RUN chown ${USERNAME}:${GROUPNAME} /code
USER ${USERNAME}


# === Install Python dependencies ===
FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --link-mode=copy


# === Development server for Flask app ===
FROM base AS dev
ENV FLASK_ENV=development
COPY --from=deps --chown=${USERNAME}:${GROUPNAME} /code/.venv ./.venv
COPY --chown=${USERNAME}:${GROUPNAME} . .

EXPOSE 5000
CMD ["uv", "run", "flask", "-A", "server.app", "run", "--reload", "--debug", "--host=0.0.0.0"]
