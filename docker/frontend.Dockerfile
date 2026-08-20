# AgentAudit frontend image (PROJECT_SPEC_5 Part 2): multi-stage build, served by nginx.
FROM node:20-slim AS build

WORKDIR /app
COPY frontend/package.json ./package.json
RUN npm install
COPY frontend/ ./
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Uses 127.0.0.1, not localhost: on this image's musl libc, "localhost" resolves to the IPv6
# loopback (::1) before the IPv4 one despite /etc/hosts listing 127.0.0.1 first, and nginx here
# only binds the IPv4 wildcard (0.0.0.0:80, per docker/nginx.conf's bare "listen 80;") -- so a
# literal "localhost" health check gets "Connection refused" against a perfectly healthy server.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
