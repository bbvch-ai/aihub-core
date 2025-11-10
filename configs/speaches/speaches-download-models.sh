#!/bin/bash

SPEACHES_BASE_URL=http://localhost:8000

until curl --silent --fail "${SPEACHES_BASE_URL}/health" > /dev/null; do
  sleep 1
done

curl "${SPEACHES_BASE_URL}/v1/models/Systran/faster-whisper-small" -X POST
curl "${SPEACHES_BASE_URL}/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX" -X POST
