FROM mcr.microsoft.com/playwright:v1.63.0-jammy

# The base image's CA store predates the eMudhra intermediate CA compromise (2026-10) and trusts emSign ECC Root CA - G3.
# This refreshes the system store only: Chromium and Firefox compile their own root stores in, which change only with a
# Playwright release.
RUN apt-get update && \
    apt-get install -y --no-install-recommends --only-upgrade ca-certificates libnss3 && \
    rm -rf /var/lib/apt/lists/*

# Install playwright package globally (browsers are already in base image)
RUN npm install -g playwright@1.63.0

# Expose the server port
EXPOSE 3000

# Run the playwright server
CMD ["npx", "playwright", "run-server", "--port", "3000", "--host", "0.0.0.0"]
