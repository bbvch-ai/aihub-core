# Stage 1: Build the Nuxt application
# Use the current (latest) version of Node.js
FROM node:25-alpine AS builder

# Install corepack (no longer bundled with Node.js as of v25). Remove the
# pre-shipped yarn shim so the corepack install does not collide with it.
# Pinned + --ignore-scripts to satisfy supply-chain security policy.
RUN rm -f /usr/local/bin/yarn /usr/local/bin/yarnpkg \
 && npm install -g --ignore-scripts corepack@0.34.7

# Set working directory
WORKDIR /app

# Copy package files to leverage Docker layer caching
COPY package.json pnpm-lock.yaml ./

# Install the exact pnpm version pinned (with SHA512 integrity check) in
# package.json's "packageManager" field. Single source of truth.
RUN corepack enable && corepack install

# Install dependencies securely and efficiently
RUN pnpm install --frozen-lockfile --ignore-scripts

# Copy the rest of the application source code
COPY . .

# Build the application for production
RUN pnpm run build

# Stage 2: Serve the static files with Nginx
# Use a lightweight and stable Nginx image
FROM nginx:stable-alpine

# Setup users
ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN addgroup -g "$USER_GID" "$USERNAME" \
  && adduser -D -H -u "$USER_UID" -G "$USERNAME" -s /sbin/nologin "$USERNAME"

# Install 'gettext' to get the 'envsubst' utility
RUN apk add --no-cache gettext

# Copy built Nuxt app
COPY --from=builder /app/.app/.output/public /usr/share/nginx/html

# Copy the Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the config template
COPY config.template.json /usr/share/nginx/html/config.template.json

# Expose port 80
EXPOSE 80

# Generate config from template and start Nginx on container startup.
# This replaces the need for an entrypoint.sh script.
CMD ["/bin/sh", "-c", "envsubst < /usr/share/nginx/html/config.template.json > /usr/share/nginx/html/config.json && nginx -g 'daemon off;'"]

