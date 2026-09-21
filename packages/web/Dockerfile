# Stage 1: Build the Nuxt application as part of the pnpm workspace.
# Build context is the monorepo root (set in docker-compose template and CI),
# so the workspace lockfile resolves deterministically.
FROM node:25-alpine AS builder

# Install corepack (no longer bundled with Node.js as of v25). Remove the
# pre-shipped yarn shim so the corepack install does not collide with it.
# Pinned + --ignore-scripts to satisfy supply-chain security policy.
RUN rm -f /usr/local/bin/yarn /usr/local/bin/yarnpkg \
 && npm install -g --ignore-scripts corepack@0.34.7

WORKDIR /app

# Layer 1: workspace + package manifests only (cached unless deps change)
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY packages/web/package.json ./packages/web/package.json

# Install the exact pnpm version pinned in root package.json's "packageManager"
RUN corepack enable && corepack install

# Install dependencies — this layer is cached as long as manifests + lockfile are unchanged
RUN pnpm install --frozen-lockfile --ignore-scripts --filter @swiss-ai-hub/web...

# Layer 2: package sources (invalidates only when sources change)
COPY packages/web ./packages/web

# Build the application for production. VERSION is the release/image version
# passed by CI as a build-arg; it is baked into runtimeConfig.public.appVersion
# so the static bundle reports the exact build it was produced from. Falls back
# to packages/web/package.json when unset (local builds).
ARG VERSION=""
ENV APP_VERSION=${VERSION}
WORKDIR /app/packages/web
RUN pnpm run build

# Stage 2: Serve the static files with the unprivileged Nginx image (UID 101,
# listens on 8080 by default — no root, no privileged port).
FROM nginxinc/nginx-unprivileged:stable-alpine

USER root
RUN apk add --no-cache gettext

COPY --from=builder /app/packages/web/.app/.output/public /usr/share/nginx/html
COPY packages/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY packages/web/config.template.js /usr/share/nginx/html/config.template.js

# nginx user (UID 101) needs write access to /usr/share/nginx/html so the
# CMD's envsubst can land /config.js there at container start.
RUN chown -R nginx:nginx /usr/share/nginx/html

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --spider -q http://127.0.0.1:8080/ || exit 1

# Generate /config.js from the template and start Nginx on container startup.
CMD ["/bin/sh", "-c", "envsubst < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js && nginx -g 'daemon off;'"]
