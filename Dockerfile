# -----
FROM rust:1.62 AS smsagent-build
WORKDIR /build/smsagent
COPY smsagent/Cargo.lock .
COPY smsagent/Cargo.toml .
RUN mkdir .cargo && cargo vendor > .cargo/config
COPY smsagent /build/smsagent
RUN cargo build --release

# -----
FROM rust:1.62 AS chat-build
WORKDIR /build/chat
COPY chat/Cargo.lock .
COPY chat/Cargo.toml .
RUN mkdir .cargo && cargo vendor > .cargo/config
COPY chat /build/chat
RUN cargo build --release

# -----
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i 's/archive.ubuntu.com/mirrors.tencent.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tencent.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3-pip python3-venv locales dnsutils iproute2 netcat tini runit && \
    locale-gen zh_CN.UTF-8 && \
    pip3 install -U pip poetry gunicorn && \
    poetry config virtualenvs.create false && \
    true

ENV TERM xterm
ENV LANG zh_CN.UTF-8
ENV LANGUAGE zh_CN:en
ENV LC_ALL zh_CN.UTF-8

# -----
FROM base AS backend

ADD backend /app
WORKDIR /app
RUN poetry install --no-dev
ENV DJANGO_SETTINGS_MODULE=prod_settings
ENV PYTHONPATH=/settings
CMD ["tini", "poetry", "--", "run", "gunicorn", "-w", "4", "--reuse-port", "backend.wsgi"]


# -----
FROM base AS game

ADD src /app
WORKDIR /app
RUN poetry install --no-dev
ENV PYTHONPATH=/settings
CMD ["tini", "poetry", "--", "run", "python", "start_server.py", "proton", "--log='file:///data/log/server.log?level=INFO'", "--backend", "http://server:server@localhost:8000/graphql"]

# -----
FROM base AS smsagent
WORKDIR /app
COPY --from=smsagent-build /build/smsagent/target/release/smsagent /app/smsagent
CMD ["tini", "/app/smsagent"]


# -----
FROM base AS chat
WORKDIR /app
COPY --from=chat-build /build/chat/target/release/chat /app/chat
CMD ["tini", "/app/chat"]
