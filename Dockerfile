FROM python:3.12.9-slim-bookworm

LABEL maintainer='Arcotech'

# set working directory
WORKDIR /usr/src/app

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/src/.venv \
    UV_COMPILE_BYTECODE=1

RUN apt-get -qq update && \
    apt-get -qq --no-install-recommends -y install \
    gcc \
    default-mysql-server \
    default-libmysqlclient-dev \
    libcurl4-openssl-dev \
    libssl-dev  \
    pkg-config \
    procps \
    # Manim dependencies
    libcairo2-dev \
    libpango1.0-dev \
    ffmpeg \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-science \
    dvipng \
    dvisvgm \
    cm-super && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /bin/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable --no-dev --verbose

# Add venv bin to PATH.
ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}"

COPY ./ ./

COPY ./entrypoint.sh /sbin/entrypoint.sh
RUN sed -i 's/\r$//g' /sbin/entrypoint.sh && chmod +x /sbin/entrypoint.sh

ENTRYPOINT ["/sbin/entrypoint.sh"]
