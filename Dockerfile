# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.3
FROM python:${PYTHON_VERSION}-slim as base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ARG UID=10001
RUN adduser \
--disabled-password \
--shell "/sbin/nologin" \
--uid "${UID}" \
sysadmin

WORKDIR /home/sysadmin/deploy
# Install dependencies
# Includes curl, and build tools needed by Poetry and many packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libffi-dev libpq-dev libssl-dev make \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
    && apt-get remove -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./
# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Copy the rest of the application
COPY . .

RUN chown -R sysadmin:sysadmin .

# Make gunicorn.sh executable
RUN chmod +x ./gunicorn.sh
# Switch to non-root user
USER sysadmin
EXPOSE 8000
# Using original command
CMD ["./gunicorn.sh"]