FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
ARG ALIASMODE_VERSION=0.1.0-beta.74
ARG ALIASMODE_SHA256=acd11f5f94f2e891b6e4ea043232bae06bcd09c8f4d71204aba26e5d06fe3984
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl python3 supervisor xvfb x11vnc novnc websockify openbox x11-utils \
    dbus-x11 fonts-liberation libwebkit2gtk-4.1-0 libnss3 libgbm1 libasound2 \
    libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgtk-3-0 libxt6 libx11-xcb1 libdbus-glib-1-2 zstd \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fL --retry 3 -o /tmp/aliasmode.tar.gz \
    "https://github.com/aliasmode/aliasmode/releases/download/v${ALIASMODE_VERSION}/AliasMode_${ALIASMODE_VERSION}_x86_64-linux.tar.gz" \
    && echo "${ALIASMODE_SHA256}  /tmp/aliasmode.tar.gz" | sha256sum -c - \
    && mkdir -p /opt/aliasmode && tar -xzf /tmp/aliasmode.tar.gz -C /opt/aliasmode --strip-components=1 \
    && rm /tmp/aliasmode.tar.gz \
    && useradd --create-home --uid 1000 --shell /bin/bash runner
COPY --chown=runner:runner . /opt/kit
RUN chmod +x /opt/kit/container/*.sh && mkdir /data && chown runner:runner /data
USER runner
ENV HOME=/home/runner DISPLAY=:99 XDG_DATA_HOME=/data XDG_CONFIG_HOME=/data/config \
    XDG_CACHE_HOME=/data/cache XDG_RUNTIME_DIR=/tmp/runner-runtime \
    WEBKIT_DISABLE_DMABUF_RENDERER=1 LIBGL_ALWAYS_SOFTWARE=1
WORKDIR /opt/kit
EXPOSE 6080
HEALTHCHECK --interval=20s --timeout=5s --start-period=60s --retries=6 \
    CMD curl -fsS http://127.0.0.1:6080/vnc.html >/dev/null || exit 1
ENTRYPOINT ["/opt/kit/container/entrypoint.sh"]
