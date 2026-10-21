# Presidio analyzer with GLiNER's multilingual PII model and spaCy's German pipeline baked in.
#
# The recognizer config (Swiss and international patterns, GLiNER labels) is NOT baked in: compose mounts it from
# infra/configs/presidio/analyzer.yaml, so pattern changes need no rebuild. Every text is analysed under the language
# code `de`; GLiNER is multilingual, so French, Italian and English text sent as `de` is covered too, and one language
# means one GLiNER copy in memory. spaCy only supplies tokens and lemmas.
#
# Models are downloaded at build time and the Hugging Face hub is offline at run time, so the container needs no
# outbound internet (it sits on the internal `pii-detection` network). app.py is Presidio's stock REST server plus an
# API-key check, because the stock server has no authentication.
#
# Re-publish via `make -C infra/deployment build-and-push-presidio-analyzer-image` or the
# "Build Presidio analyzer image" workflow after editing this file, then bump image_tags.presidio_analyzer.
FROM python:3.12-slim

# Torch's default thread count oversubscribes a shared host: a short request took seconds instead of ~250 ms.
ENV PIP_NO_CACHE_DIR=1 PORT=3000 ANALYZER_CONF_FILE=/app/analyzer.yaml HF_HOME=/app/hf OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4

WORKDIR /app

RUN useradd -m -u 1001 presidio && chown presidio:presidio /app

RUN pip install "torch==2.14.1" --index-url https://download.pytorch.org/whl/cpu \
    && pip install "presidio-analyzer[server,gliner]==2.2.364" "gliner==0.2.29" \
    https://github.com/explosion/spacy-models/releases/download/de_core_news_lg-3.8.0/de_core_news_lg-3.8.0-py3-none-any.whl

USER 1001

# Downloaded as the runtime user so the weights are not duplicated into a second layer by a later chown. Presidio
# loads the model by name, i.e. revision `main`, so refs/main is pointed at the pinned revision for the offline hub.
ARG GLINER_REVISION=1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d
RUN python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_multi_pii-v1', \
    revision='${GLINER_REVISION}')" \
    && mkdir -p "${HF_HOME}/hub/models--urchade--gliner_multi_pii-v1/refs" \
    && printf '%s' "${GLINER_REVISION}" > "${HF_HOME}/hub/models--urchade--gliner_multi_pii-v1/refs/main"

COPY --chown=1001:1001 app.py word_aligned_text_chunker.py logging.ini /app/

ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

EXPOSE 3000
# A 20k-token prompt takes about a minute on 4 CPU threads; the stock 120 s worker timeout leaves too little headroom.
CMD ["sh", "-c", "gunicorn -w 1 -b 0.0.0.0:${PORT} --timeout 300 'app:create_app()'"]
