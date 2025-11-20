#!/usr/bin/env bash

# Simple watchdog for LocalTunnel. Launches `lt` with the desired port/subdomain
# and keeps it alive by periodically health-checking the public URL.

set -euo pipefail

# Configuration (override via environment variables when invoking the script)
PORT="${PORT:-8005}"
SUBDOMAIN="${SUBDOMAIN:-dbcv-mcp}"
URL="${URL:-https://${SUBDOMAIN}.loca.lt}"
CHECK_URL="${CHECK_URL:-${URL}/health}"
LT_BIN="${LT_BIN:-lt}"
CHECK_INTERVAL="${CHECK_INTERVAL:-10}"
PID_FILE="${PID_FILE:-/tmp/localtunnel_${PORT}.pid}"

log() {
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >&2
}

start_localtunnel() {
    log "Starting LocalTunnel on port ${PORT} with subdomain ${SUBDOMAIN}..."
    "${LT_BIN}" --port "${PORT}" --subdomain "${SUBDOMAIN}" >/dev/null 2>&1 &
    LT_PID=$!
    echo "${LT_PID}" >"${PID_FILE}"

    # Wait a moment for the tunnel to come up
    sleep 5

    if ! kill -0 "${LT_PID}" 2>/dev/null; then
        log "Failed to start LocalTunnel process. Check that 'lt' is installed and reachable."
        rm -f "${PID_FILE}"
        return 1
    fi

    log "LocalTunnel PID ${LT_PID} is up. Public URL: ${URL}"
}

stop_localtunnel() {
    if [ -f "${PID_FILE}" ]; then
        LT_PID=$(cat "${PID_FILE}")
        if kill -0 "${LT_PID}" 2>/dev/null; then
            log "Stopping LocalTunnel process ${LT_PID}..."
            kill "${LT_PID}" 2>/dev/null || true
            # Wait briefly for a graceful shutdown
            for _ in {1..5}; do
                if ! kill -0 "${LT_PID}" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            if kill -0 "${LT_PID}" 2>/dev/null; then
                log "Process still alive; forcing termination."
                kill -9 "${LT_PID}" 2>/dev/null || true
            fi
        fi
        rm -f "${PID_FILE}"
    fi

    # Optional: free the port if anything else is listening
    if command -v lsof >/dev/null 2>&1; then
        listeners=$(lsof -t -i :"${PORT}" -sTCP:LISTEN || true)
        if [ -n "${listeners}" ]; then
            log "Killing listeners on port ${PORT}: ${listeners}"
            kill -9 ${listeners} 2>/dev/null || true
        fi
    fi
}

cleanup() {
    log "Received termination signal. Cleaning up..."
    stop_localtunnel
    exit 0
}

trap cleanup INT TERM

log "Preparing LocalTunnel watchdog."
stop_localtunnel
start_localtunnel

while true; do
    sleep "${CHECK_INTERVAL}"

    HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}" --connect-timeout 5 --max-time 10 "${CHECK_URL}" || echo "000")
    if [[ "${HTTP_STATUS}" != "200" ]]; then
        log "LocalTunnel health check failed for ${CHECK_URL} (HTTP ${HTTP_STATUS}). Restarting tunnel..."
        stop_localtunnel
        start_localtunnel
    fi
done
