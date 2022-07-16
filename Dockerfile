# -----
FROM rust:1.62 AS smsagent-build
WORKDIR /build/smsagent
COPY deploy/cargo-config .cargo/config
COPY smsagent/Cargo.lock .
COPY smsagent/Cargo.toml .
RUN cargo vendor --respect-source-config > .cargo/config.vendor && mv .cargo/config.vendor .cargo/config
COPY smsagent /build/smsagent
RUN cargo build --release

# -----
FROM rust:1.62 AS chat-build
WORKDIR /build/chat
COPY deploy/cargo-config .cargo/config
COPY chat/Cargo.lock .
COPY chat/Cargo.toml .
RUN cargo vendor --respect-source-config > .cargo/config.vendor && mv .cargo/config.vendor .cargo/config
COPY chat /build/chat
RUN cargo build --release

# -----
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV POETRY_HOME=/usr/local
RUN sed -i 's/archive.ubuntu.com/mirrors.tencent.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tencent.com/g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3 python3-venv locales dnsutils iproute2 netcat tini runit vim curl && \
    locale-gen zh_CN.UTF-8 && \
    curl https://bootstrap.pypa.io/get-pip.py | python3 - && \
    curl https://install.python-poetry.org/ | python3 - && \
    poetry config virtualenvs.create false && \
    true

ENV TERM xterm
ENV LANG zh_CN.UTF-8
ENV LANGUAGE zh_CN:en
ENV LC_ALL zh_CN.UTF-8

# -----
FROM base AS backend

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/poetry.lock ./
RUN poetry install --no-dev
ADD backend /app
CMD ["tini", "/bin/bash", "--", "-c", "exec poetry run gunicorn -b 0.0.0.0:8000 -w 4 --reuse-port backend.wsgi"]

# -----
FROM backend AS backend-static
ENV SECRET_KEY=dummy
RUN poetry run python3 manage.py collectstatic --no-input

# -----
FROM base AS game

WORKDIR /app
COPY src/pyproject.toml ./
COPY src/poetry.lock ./
RUN poetry install --no-dev
ADD src /app
CMD ["tini", "/bin/bash", "--", "-c", "exec poetry run python3 start_server.py $INSTANCE --log='file:///data/thb/server.log?level=INFO' --backend $BACKEND_URL --archive-path /data/thb/archive --interconnect \"$INTERCONNECT_URL\""]

# # -----
# FROM base AS smsagent
# WORKDIR /app
# COPY --from=smsagent-build /build/smsagent/target/release/smsagent /app/smsagent
# CMD ["tini", "/app/smsagent"]


# -----
FROM base AS chat
WORKDIR /app
COPY --from=chat-build /build/chat/target/release/chat /app/chat
CMD ["tini", "/bin/bash", "--", "-c", "exec /app/chat --backend $BACKEND_URL"]

# -----
FROM openresty/openresty:1.21.4.1-jammy AS nginx
RUN luarocks install lua-resty-auto-ssl
COPY --from=backend-static /app/static-root /var/www/backend-static

# -----
FROM postgres:14 AS db
RUN localedef -i zh_CN -c -f UTF-8 -A /usr/share/locale/locale.alias zh_CN.UTF-8
ENV LANG zh_CN.utf8

# -----
FROM base AS lvs
RUN apt-get -y install ipvsadm
ADD deploy/container-lvs.sh /container-lvs.sh
CMD ["/container-lvs.sh"]

# -----
FROM base AS redis
RUN apt-get -y install redis-server
CMD ["tini", "redis-server", "--", "--bind", "0.0.0.0", "--dbfilename", "redis.rdb", "--dir", "/var/lib/redis", "--save", "15", "1"]
