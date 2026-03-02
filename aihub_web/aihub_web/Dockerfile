# Stage 1: Build the Nuxt application
# Use the Long-Term Support (LTS) version of Node.js for stability
FROM node:20-alpine AS builder

# Enable and prepare pnpm via corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Set working directory
WORKDIR /app

# Copy package files to leverage Docker layer caching
COPY package.json pnpm-lock.yaml ./

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

