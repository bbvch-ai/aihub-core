FROM ghcr.io/docling-project/docling-serve-cu124:latest

# Set working directory
WORKDIR /app

# Create models directory and set permissions
RUN mkdir -p /app/models && chmod -R 777 /app/models

# Download models during image build (this will be cached in the image)
RUN echo 'Downloading models...' && \
    docling-tools models download --output-dir /app/models layout tableformer code_formula easyocr && \
    echo 'Models downloaded successfully!'

# Set environment variables
ENV DOCLING_SERVE_ARTIFACTS_PATH=/app/models
ENV DOCLING_SERVE_ENABLE_UI=true

# Expose port
EXPOSE 5001

# Set the default command
CMD ["docling-serve", "run"]