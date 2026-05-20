FROM mcr.microsoft.com/playwright:v1.60.0-jammy

# Install playwright package globally (browsers are already in base image)
RUN npm install -g playwright@1.60.0

# Expose the server port
EXPOSE 3000

# Run the playwright server
CMD ["npx", "playwright", "run-server", "--port", "3000", "--host", "0.0.0.0"]
