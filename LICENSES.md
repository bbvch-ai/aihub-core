# License Report

Generated on: 11.12.2025

This document contains license information for all dependencies across the monorepo:

- Python packages (Poetry): **236 packages**
- Node.js packages (pnpm): **197 packages**
- External Docker images: **30 images**

### License Compatibility

✅ **All dependencies have approved licenses!**

### Legend

- ✅ = Permissive or Manually Approved License
- ⚠️ = License requires manual review and approval
- ❌ = Restrictive or Unknown License

### License Compatibility

## Python Dependencies

### aihub_lib

| Status | Package                                      | Version           | License                                           | Notes |
| ------ | -------------------------------------------- | ----------------- | ------------------------------------------------- | ----- |
| ✅     | protobuf                                     | 5.29.5            | 3-Clause BSD License                              |       |
| ✅     | dirtyjson                                    | 1.0.8             | Academic Free License (AFL); MIT License          |       |
| ✅     | asttokens                                    | 3.0.0             | Apache 2.0                                        |       |
| ✅     | multidict                                    | 6.7.0             | Apache License 2.0                                |       |
| ✅     | aiosignal                                    | 1.4.0             | Apache Software License                           |       |
| ✅     | distro                                       | 1.9.0             | Apache Software License                           |       |
| ✅     | googleapis-common-protos                     | 1.71.0            | Apache Software License                           |       |
| ✅     | grpcio                                       | 1.76.0            | Apache Software License                           |       |
| ✅     | huggingface-hub                              | 0.36.0            | Apache Software License                           |       |
| ✅     | importlib_metadata                           | 8.7.0             | Apache Software License                           |       |
| ✅     | jsonpath-ng                                  | 1.7.0             | Apache Software License                           |       |
| ✅     | motor                                        | 3.7.1             | Apache Software License                           |       |
| ✅     | nats-py                                      | 2.12.0            | Apache Software License                           |       |
| ✅     | nltk                                         | 3.9.2             | Apache Software License                           |       |
| ✅     | openai                                       | 1.109.1           | Apache Software License                           |       |
| ✅     | opentelemetry-instrumentation-milvus         | 0.47.5            | Apache Software License                           |       |
| ✅     | opentelemetry-semantic-conventions-ai        | 0.4.13            | Apache Software License                           |       |
| ✅     | propcache                                    | 0.4.1             | Apache Software License                           |       |
| ✅     | pyarrow                                      | 22.0.0            | Apache Software License                           |       |
| ✅     | pymilvus                                     | 2.6.3             | Apache Software License                           |       |
| ✅     | pymongo                                      | 4.15.3            | Apache Software License                           |       |
| ✅     | pytest-asyncio                               | 0.24.0            | Apache Software License                           |       |
| ✅     | requests                                     | 2.32.5            | Apache Software License                           |       |
| ✅     | s3transfer                                   | 0.14.0            | Apache Software License                           |       |
| ✅     | safetensors                                  | 0.6.2             | Apache Software License                           |       |
| ✅     | tenacity                                     | 9.1.2             | Apache Software License                           |       |
| ✅     | tokenizers                                   | 0.22.1            | Apache Software License                           |       |
| ✅     | transformers                                 | 4.57.1            | Apache Software License                           |       |
| ✅     | tzdata                                       | 2025.2            | Apache Software License                           |       |
| ✅     | yarl                                         | 1.22.0            | Apache Software License                           |       |
| ✅     | packaging                                    | 25.0              | Apache Software License; BSD License              |       |
| ✅     | python-dateutil                              | 2.9.0.post0       | Apache Software License; BSD License              |       |
| ✅     | sniffio                                      | 1.3.1             | Apache Software License; MIT License              |       |
| ✅     | regex                                        | 2025.11.3         | Apache-2.0 (override)                             |       |
| ✅     | aiohttp                                      | 3.13.2            | Apache-2.0 AND MIT                                |       |
| ✅     | cryptography                                 | 46.0.3            | Apache-2.0 OR BSD-3-Clause                        |       |
| ✅     | orjson                                       | 3.11.4            | Apache-2.0 OR MIT                                 |       |
| ✅     | arize-phoenix-otel                           | 0.13.1            | Apache-2.0                                        |       |
| ✅     | boto3                                        | 1.40.66           | Apache-2.0                                        |       |
| ✅     | botocore                                     | 1.40.66           | Apache-2.0                                        |       |
| ✅     | coverage                                     | 7.11.0            | Apache-2.0                                        |       |
| ✅     | frozenlist                                   | 1.8.0             | Apache-2.0                                        |       |
| ✅     | hf-xet                                       | 1.2.0             | Apache-2.0 (override)                             |       |
| ✅     | openinference-instrumentation                | 0.1.42            | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation-llama-index    | 4.3.8             | Apache-2.0                                        |       |
| ✅     | openinference-semantic-conventions           | 0.1.25            | Apache-2.0                                        |       |
| ✅     | opentelemetry-api                            | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp                  | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-common     | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc       | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-http       | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-instrumentation                | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-asyncio        | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-botocore       | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-httpx          | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-jinja2         | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-logging        | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-pymongo        | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-redis          | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-requests       | 0.58b0            | Apache-2.0                                        |       |
| ✅     | opentelemetry-propagator-aws-xray            | 1.0.2             | Apache-2.0                                        |       |
| ✅     | opentelemetry-proto                          | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-sdk                            | 1.37.0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-semantic-conventions           | 0.58b0            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-util-http                      | 0.58b0            | Apache-2.0                                        |       |
| ✅     | python-multipart                             | 0.0.20            | Apache-2.0                                        |       |
| ✅     | types-PyYAML                                 | 6.0.12.20250915   | Apache-2.0 (override)                             |       |
| ✅     | types-networkx                               | 3.5.0.20251104    | Apache-2.0 (override)                             |       |
| ✅     | types-pytz                                   | 2025.2.0.20251108 | Apache-2.0                                        |       |
| ✅     | types-requests                               | 2.32.4.20250913   | Apache-2.0 (override)                             |       |
| ✅     | Authlib                                      | 1.6.5             | BSD License                                       |       |
| ✅     | Jinja2                                       | 3.1.6             | BSD License                                       |       |
| ✅     | Pygments                                     | 2.19.2            | BSD License                                       |       |
| ✅     | adlfs                                        | 2024.12.0         | BSD License                                       |       |
| ✅     | colorama                                     | 0.4.6             | BSD License                                       |       |
| ✅     | contourpy                                    | 1.3.3             | BSD License                                       |       |
| ✅     | cycler                                       | 0.12.1            | BSD License                                       |       |
| ✅     | decorator                                    | 5.2.1             | BSD License                                       |       |
| ✅     | flatdict                                     | 4.0.1             | BSD License                                       |       |
| ✅     | fsspec                                       | 2024.12.0         | BSD License                                       |       |
| ✅     | httpx                                        | 0.28.1            | BSD License                                       |       |
| ✅     | ipython_pygments_lexers                      | 1.1.1             | BSD License                                       |       |
| ✅     | isodate                                      | 0.7.2             | BSD License                                       |       |
| ✅     | joblib                                       | 1.5.2             | BSD License                                       |       |
| ✅     | kiwisolver                                   | 1.4.9             | BSD License                                       |       |
| ✅     | lxml                                         | 5.4.0             | BSD License                                       |       |
| ✅     | nest-asyncio                                 | 1.6.0             | BSD License                                       |       |
| ✅     | networkx                                     | 3.5               | BSD License                                       |       |
| ✅     | numpy                                        | 2.3.4             | BSD License                                       |       |
| ✅     | pandas                                       | 2.2.3             | BSD License                                       |       |
| ✅     | pandas-stubs                                 | 2.3.3.251201      | BSD License                                       |       |
| ✅     | prompt_toolkit                               | 3.0.52            | BSD License                                       |       |
| ✅     | pycparser                                    | 2.23              | BSD License                                       |       |
| ✅     | scipy                                        | 1.16.3            | BSD License                                       |       |
| ✅     | striprtf                                     | 0.0.26            | BSD License                                       |       |
| ✅     | threadpoolctl                                | 3.6.0             | BSD License                                       |       |
| ✅     | traitlets                                    | 5.14.3            | BSD License                                       |       |
| ✅     | webencodings                                 | 0.5.1             | BSD License                                       |       |
| ✅     | wrapt                                        | 1.17.3            | BSD License                                       |       |
| ✅     | ply                                          | 3.11              | BSD                                               |       |
| ✅     | MarkupSafe                                   | 3.0.3             | BSD-3-Clause                                      |       |
| ✅     | click                                        | 8.3.0             | BSD-3-Clause (override)                           |       |
| ✅     | httpcore                                     | 1.0.9             | BSD-3-Clause                                      |       |
| ✅     | idna                                         | 3.11              | BSD-3-Clause                                      |       |
| ✅     | ipython                                      | 9.7.0             | BSD-3-Clause                                      |       |
| ✅     | psutil                                       | 7.1.3             | BSD-3-Clause                                      |       |
| ✅     | pypdf                                        | 5.9.0             | BSD-3-Clause (override)                           |       |
| ✅     | python-dotenv                                | 1.2.1             | BSD-3-Clause                                      |       |
| ✅     | scikit-learn                                 | 1.7.2             | BSD-3-Clause (override)                           |       |
| ✅     | starlette                                    | 0.46.2            | BSD-3-Clause                                      |       |
| ✅     | uvicorn                                      | 0.38.0            | BSD-3-Clause                                      |       |
| ✅     | arize-phoenix                                | 10.15.0           | Elastic-2.0                                       |       |
| ✅     | arize-phoenix-client                         | 1.21.0            | Elastic-2.0                                       |       |
| ✅     | arize-phoenix-evals                          | 2.5.0             | Elastic-2.0                                       |       |
| ✅     | dnspython                                    | 2.8.0             | ISC License (ISCL)                                |       |
| ✅     | pexpect                                      | 4.9.0             | ISC License (ISCL)                                |       |
| ✅     | ptyprocess                                   | 0.7.0             | ISC License (ISCL)                                |       |
| ✅     | shellingham                                  | 1.5.4             | ISC License (ISCL)                                |       |
| ✅     | griffe                                       | 1.14.0            | ISC (override)                                    |       |
| ✅     | greenlet                                     | 3.2.4             | MIT AND Python-2.0                                |       |
| ✅     | Deprecated                                   | 1.3.1             | MIT License                                       |       |
| ✅     | Mako                                         | 1.3.10            | MIT License                                       |       |
| ✅     | PyJWT                                        | 2.10.1            | MIT License                                       |       |
| ✅     | PyYAML                                       | 6.0.3             | MIT License                                       |       |
| ✅     | aioitertools                                 | 0.12.0            | MIT License                                       |       |
| ✅     | aiosqlite                                    | 0.21.0            | MIT License                                       |       |
| ✅     | annotated-types                              | 0.7.0             | MIT License                                       |       |
| ✅     | azure-ai-documentintelligence                | 1.0.2             | MIT License                                       |       |
| ✅     | azure-core                                   | 1.36.0            | MIT License                                       |       |
| ✅     | azure-datalake-store                         | 0.0.53            | MIT License                                       |       |
| ✅     | azure-storage-blob                           | 12.27.1           | MIT License                                       |       |
| ✅     | azure-storage-file-datalake                  | 12.22.0           | MIT License                                       |       |
| ✅     | beautifulsoup4                               | 4.14.2            | MIT License                                       |       |
| ✅     | black                                        | 24.10.0           | MIT License                                       |       |
| ✅     | cachetools                                   | 5.5.2             | MIT License                                       |       |
| ✅     | cohere                                       | 5.20.0            | MIT License                                       |       |
| ✅     | colorlog                                     | 6.10.1            | MIT License                                       |       |
| ✅     | dataclasses-json                             | 0.6.7             | MIT License                                       |       |
| ✅     | executing                                    | 2.2.1             | MIT License                                       |       |
| ✅     | fastapi                                      | 0.115.14          | MIT License                                       |       |
| ✅     | filetype                                     | 1.2.0             | MIT License                                       |       |
| ✅     | graphql-core                                 | 3.2.7             | MIT License                                       |       |
| ✅     | grpc-interceptor                             | 0.15.4            | MIT License                                       |       |
| ✅     | h11                                          | 0.16.0            | MIT License                                       |       |
| ✅     | html5lib                                     | 1.1               | MIT License                                       |       |
| ✅     | jedi                                         | 0.19.2            | MIT License                                       |       |
| ✅     | jiter                                        | 0.11.1            | MIT License                                       |       |
| ✅     | jmespath                                     | 1.0.1             | MIT License                                       |       |
| ✅     | latex2mathml                                 | 3.78.1            | MIT License                                       |       |
| ✅     | llama-index-embeddings-openai                | 0.3.1             | MIT License                                       |       |
| ✅     | llama-index-postprocessor-cohere-rerank      | 0.3.0             | MIT License                                       |       |
| ✅     | llama-index-storage-docstore-mongodb         | 0.3.0             | MIT License                                       |       |
| ✅     | llama-index-storage-kvstore-mongodb          | 0.3.0             | MIT License                                       |       |
| ✅     | markdown-it-py                               | 4.0.0             | MIT License                                       |       |
| ✅     | marshmallow                                  | 3.26.1            | MIT License                                       |       |
| ✅     | mdurl                                        | 0.1.2             | MIT License                                       |       |
| ✅     | mongoengine                                  | 0.29.1            | MIT License                                       |       |
| ✅     | msal                                         | 1.34.0            | MIT License                                       |       |
| ✅     | msal-extensions                              | 1.3.1             | MIT License                                       |       |
| ✅     | mypy                                         | 1.18.2            | MIT License                                       |       |
| ✅     | parse                                        | 1.20.2            | MIT License                                       |       |
| ✅     | parso                                        | 0.8.5             | MIT License                                       |       |
| ✅     | pluggy                                       | 1.6.0             | MIT License                                       |       |
| ✅     | pure_eval                                    | 0.2.3             | MIT License                                       |       |
| ✅     | pystache                                     | 0.6.8             | MIT License                                       |       |
| ✅     | pytest                                       | 8.4.2             | MIT License                                       |       |
| ✅     | pytest-bdd                                   | 8.1.0             | MIT License                                       |       |
| ✅     | pytest-mock                                  | 3.15.1            | MIT License                                       |       |
| ✅     | python-i18n                                  | 0.3.9             | MIT License                                       |       |
| ✅     | pytz                                         | 2025.2            | MIT License                                       |       |
| ✅     | redis                                        | 5.3.1             | MIT License                                       |       |
| ✅     | rich                                         | 14.2.0            | MIT License                                       |       |
| ✅     | ruff                                         | 0.8.6             | MIT License                                       |       |
| ✅     | six                                          | 1.17.0            | MIT License                                       |       |
| ✅     | stack-data                                   | 0.6.3             | MIT License                                       |       |
| ✅     | strawberry-graphql                           | 0.270.1           | MIT License                                       |       |
| ✅     | tabulate                                     | 0.9.0             | MIT License                                       |       |
| ✅     | toml-sort                                    | 0.24.3            | MIT License                                       |       |
| ✅     | tomlkit                                      | 0.13.3            | MIT License                                       |       |
| ✅     | typer                                        | 0.19.2            | MIT License                                       |       |
| ✅     | typing-inspect                               | 0.9.0             | MIT License                                       |       |
| ✅     | tqdm                                         | 4.67.1            | MIT License; Mozilla Public License 2.0 (MPL 2.0) |       |
| ✅     | tiktoken                                     | 0.12.0            | MIT (override)                                    |       |
| ✅     | SQLAlchemy                                   | 2.0.44            | MIT                                               |       |
| ✅     | alembic                                      | 1.17.1            | MIT (override)                                    |       |
| ✅     | anyio                                        | 4.11.0            | MIT (override)                                    |       |
| ✅     | attrs                                        | 25.4.0            | MIT (override)                                    |       |
| ✅     | azure-identity                               | 1.25.1            | MIT                                               |       |
| ✅     | banks                                        | 2.2.0             | BSD-3-Clause (override)                           |       |
| ✅     | cffi                                         | 2.0.0             | MIT                                               |       |
| ✅     | charset-normalizer                           | 3.4.4             | MIT                                               |       |
| ✅     | docling-core                                 | 2.54.1            | MIT (override)                                    |       |
| ✅     | fastavro                                     | 1.12.1            | MIT                                               |       |
| ✅     | fonttools                                    | 4.60.1            | MIT                                               |       |
| ✅     | gherkin-official                             | 29.0.0            | MIT                                               |       |
| ✅     | httpx-sse                                    | 0.4.0             | MIT                                               |       |
| ✅     | iniconfig                                    | 2.3.0             | MIT                                               |       |
| ✅     | jsonref                                      | 1.1.0             | MIT                                               |       |
| ✅     | jsonschema                                   | 4.25.1            | MIT (override)                                    |       |
| ✅     | jsonschema-specifications                    | 2025.9.1          | MIT (override)                                    |       |
| ✅     | llama-index-core                             | 0.12.52.post1     | MIT (override)                                    |       |
| ✅     | llama-index-embeddings-openai-like           | 0.1.1             | MIT (override)                                    |       |
| ✅     | llama-index-instrumentation                  | 0.4.2             | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai                      | 0.3.44            | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai-like                 | 0.3.5             | MIT (override)                                    |       |
| ✅     | llama-index-readers-file                     | 0.4.11            | MIT (override)                                    |       |
| ✅     | llama-index-vector-stores-milvus             | 0.8.7             | MIT (override)                                    |       |
| ✅     | llama-index-workflows                        | 1.3.0             | MIT (override)                                    |       |
| ✅     | mypy_extensions                              | 1.1.0             | MIT (override)                                    |       |
| ✅     | parse_type                                   | 0.6.6             | MIT (override)                                    |       |
| ✅     | platformdirs                                 | 4.5.0             | MIT                                               |       |
| ✅     | pydantic                                     | 2.12.4            | MIT                                               |       |
| ✅     | pydantic-settings                            | 2.11.0            | MIT                                               |       |
| ✅     | pydantic_core                                | 2.41.5            | MIT                                               |       |
| ✅     | pyparsing                                    | 3.2.5             | MIT                                               |       |
| ✅     | pytest-cov                                   | 6.3.0             | MIT                                               |       |
| ✅     | referencing                                  | 0.37.0            | MIT (override)                                    |       |
| ✅     | rpds-py                                      | 0.28.0            | MIT (override)                                    |       |
| ✅     | soupsieve                                    | 2.8               | MIT                                               |       |
| ✅     | tokenize_rt                                  | 6.2.0             | MIT                                               |       |
| ✅     | typing-inspection                            | 0.4.2             | MIT (override)                                    |       |
| ✅     | urllib3                                      | 2.5.0             | MIT (override)                                    |       |
| ✅     | zipp                                         | 3.23.0            | MIT (override)                                    |       |
| ✅     | pillow                                       | 12.0.0            | MIT-CMU (override)                                |       |
| ✅     | certifi                                      | 2025.10.5         | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | pathspec                                     | 0.12.1            | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | typing_extensions                            | 4.15.0            | PSF-2.0 (override)                                |       |
| ✅     | aiohappyeyeballs                             | 2.6.1             | Python Software Foundation License                |       |
| ✅     | defusedxml                                   | 0.7.1             | Python Software Foundation License                |       |
| ✅     | matplotlib                                   | 3.10.7            | Python Software Foundation License                |       |
| ✅     | email-validator                              | 2.3.0             | The Unlicense (Unlicense)                         |       |
| ✅     | matplotlib-inline                            | 0.2.1             | BSD-3-Clause (override)                           |       |
| ✅     | filelock                                     | 3.20.0            | Unlicense                                         |       |
| ✅     | sqlean.py                                    | 3.50.4.5          | zlib/libpng                                       |       |

## JavaScript/TypeScript Dependencies

### aihub_web (Node.js)

| Status | Package                            | Version | License                                       | Notes |
| ------ | ---------------------------------- | ------- | --------------------------------------------- | ----- |
| ✅     | @babel/helper-string-parser        | 7.27.1  | MIT                                           |       |
| ✅     | @babel/helper-validator-identifier | 7.27.1  | MIT                                           |       |
| ✅     | @babel/parser                      | 7.28.4  | MIT                                           |       |
| ✅     | @babel/types                       | 7.28.4  | MIT                                           |       |
| ✅     | @dagrejs/dagre                     | 1.1.5   | MIT                                           |       |
| ✅     | @dagrejs/graphlib                  | 2.2.4   | MIT                                           |       |
| ✅     | @floating-ui/core                  | 1.7.3   | MIT                                           |       |
| ✅     | @floating-ui/dom                   | 1.7.4   | MIT                                           |       |
| ✅     | @floating-ui/utils                 | 0.2.10  | MIT                                           |       |
| ✅     | @floating-ui/vue                   | 1.1.9   | MIT                                           |       |
| ✅     | @hey-api/client-fetch              | 0.12.0  | MIT                                           |       |
| ✅     | @hey-api/json-schema-ref-parser    | 1.0.6   | MIT                                           |       |
| ✅     | @hey-api/openapi-ts                | 0.71.1  | MIT                                           |       |
| ✅     | @internationalized/date            | 3.9.0   | Apache-2.0                                    |       |
| ✅     | @internationalized/number          | 3.6.5   | Apache-2.0                                    |       |
| ✅     | @jridgewell/gen-mapping            | 0.3.13  | MIT                                           |       |
| ✅     | @jridgewell/remapping              | 2.3.5   | MIT                                           |       |
| ✅     | @jridgewell/resolve-uri            | 3.1.2   | MIT                                           |       |
| ✅     | @jridgewell/sourcemap-codec        | 1.5.5   | MIT                                           |       |
| ✅     | @jridgewell/trace-mapping          | 0.3.31  | MIT                                           |       |
| ✅     | @jsdevtools/ono                    | 7.1.3   | MIT                                           |       |
| ✅     | @nuxt/kit                          | 3.19.2  | MIT                                           |       |
| ✅     | @pinia/colada                      | 0.17.6  | MIT                                           |       |
| ✅     | @pinia/colada-nuxt                 | 0.2.3   | MIT                                           |       |
| ✅     | @pinia/nuxt                        | 0.11.2  | MIT                                           |       |
| ✅     | @primeuix/forms                    | 0.1.0   | MIT                                           |       |
| ✅     | @primeuix/styled                   | 0.6.4   | MIT                                           |       |
| ✅     | @primeuix/styles                   | 1.2.5   | MIT                                           |       |
| ✅     | @primeuix/themes                   | 1.1.1   | MIT                                           |       |
| ✅     | @primeuix/utils                    | 0.5.4   | MIT                                           |       |
| ✅     | @primevue/core                     | 4.3.6   | MIT                                           |       |
| ✅     | @primevue/forms                    | 4.3.9   | MIT                                           |       |
| ✅     | @primevue/icons                    | 4.3.6   | MIT                                           |       |
| ✅     | @socket.io/component-emitter       | 3.1.2   | MIT                                           |       |
| ✅     | @svgdotjs/svg.draggable.js         | 3.0.6   | MIT                                           |       |
| ✅     | @svgdotjs/svg.filter.js            | 3.0.9   | MIT                                           |       |
| ✅     | @svgdotjs/svg.js                   | 3.2.5   | MIT                                           |       |
| ✅     | @svgdotjs/svg.resize.js            | 2.0.5   | MIT                                           |       |
| ✅     | @svgdotjs/svg.select.js            | 4.0.3   | MIT                                           |       |
| ✅     | @swc/helpers                       | 0.5.17  | Apache-2.0                                    |       |
| ✅     | @tanstack/virtual-core             | 3.13.12 | MIT                                           |       |
| ✅     | @tanstack/vue-virtual              | 3.13.12 | MIT                                           |       |
| ✅     | @types/estree                      | 1.0.8   | MIT                                           |       |
| ✅     | @types/json-schema                 | 7.0.15  | MIT                                           |       |
| ✅     | @types/web-bluetooth               | 0.0.20  | MIT                                           |       |
| ✅     | @vue-flow/background               | 1.3.2   | MIT                                           |       |
| ✅     | @vue-flow/controls                 | 1.1.3   | MIT                                           |       |
| ✅     | @vue-flow/core                     | 1.46.5  | MIT                                           |       |
| ✅     | @vue-flow/minimap                  | 1.5.4   | MIT                                           |       |
| ✅     | @vue/compiler-core                 | 3.5.17  | MIT                                           |       |
| ✅     | @vue/compiler-dom                  | 3.5.17  | MIT                                           |       |
| ✅     | @vue/compiler-sfc                  | 3.5.17  | MIT                                           |       |
| ✅     | @vue/compiler-ssr                  | 3.5.17  | MIT                                           |       |
| ✅     | @vue/devtools-api                  | 6.6.4   | MIT                                           |       |
| ✅     | @vue/devtools-kit                  | 7.7.7   | MIT                                           |       |
| ✅     | @vue/devtools-shared               | 7.7.7   | MIT                                           |       |
| ✅     | @vue/reactivity                    | 3.5.17  | MIT                                           |       |
| ✅     | @vue/runtime-core                  | 3.5.17  | MIT                                           |       |
| ✅     | @vue/runtime-dom                   | 3.5.17  | MIT                                           |       |
| ✅     | @vue/server-renderer               | 3.5.17  | MIT                                           |       |
| ✅     | @vue/shared                        | 3.5.17  | MIT                                           |       |
| ✅     | @vueuse/core                       | 10.11.1 | MIT                                           |       |
| ✅     | @vueuse/integrations               | 13.9.0  | MIT                                           |       |
| ✅     | @vueuse/math                       | 13.9.0  | MIT                                           |       |
| ✅     | @vueuse/metadata                   | 10.11.1 | MIT                                           |       |
| ✅     | @vueuse/router                     | 13.9.0  | MIT                                           |       |
| ✅     | @vueuse/shared                     | 10.11.1 | MIT                                           |       |
| ✅     | @yr/monotone-cubic-spline          | 1.0.3   | MIT                                           |       |
| ✅     | acorn                              | 8.15.0  | MIT                                           |       |
| ✅     | ansi-colors                        | 4.1.3   | MIT                                           |       |
| ✅     | apexcharts                         | 4.7.0   | MIT                                           |       |
| ✅     | argparse                           | 2.0.1   | Python Software Foundation License (override) |       |
| ✅     | aria-hidden                        | 1.2.6   | MIT                                           |       |
| ✅     | birpc                              | 2.6.1   | MIT                                           |       |
| ✅     | c12                                | 2.0.1   | MIT                                           |       |
| ✅     | change-case                        | 5.4.4   | MIT                                           |       |
| ✅     | chokidar                           | 4.0.3   | MIT                                           |       |
| ✅     | chownr                             | 2.0.0   | ISC                                           |       |
| ✅     | citty                              | 0.1.6   | MIT                                           |       |
| ✅     | class-variance-authority           | 0.7.1   | Apache-2.0                                    |       |
| ✅     | clsx                               | 2.1.1   | MIT                                           |       |
| ✅     | color-support                      | 1.1.3   | ISC                                           |       |
| ✅     | commander                          | 13.0.0  | MIT                                           |       |
| ✅     | confbox                            | 0.1.8   | MIT                                           |       |
| ✅     | consola                            | 3.4.2   | MIT                                           |       |
| ✅     | copy-anything                      | 3.0.5   | MIT                                           |       |
| ✅     | csstype                            | 3.1.3   | MIT                                           |       |
| ✅     | d3-color                           | 3.1.0   | ISC                                           |       |
| ✅     | d3-dispatch                        | 3.0.1   | ISC                                           |       |
| ✅     | d3-drag                            | 3.0.0   | ISC                                           |       |
| ✅     | d3-ease                            | 3.0.1   | BSD-3-Clause                                  |       |
| ✅     | d3-interpolate                     | 3.0.1   | ISC                                           |       |
| ✅     | d3-selection                       | 3.0.0   | ISC                                           |       |
| ✅     | d3-timer                           | 3.0.1   | ISC                                           |       |
| ✅     | d3-transition                      | 3.0.1   | ISC                                           |       |
| ✅     | d3-zoom                            | 3.0.0   | ISC                                           |       |
| ✅     | date-fns                           | 4.1.0   | MIT                                           |       |
| ✅     | debug                              | 4.3.7   | MIT                                           |       |
| ✅     | defu                               | 6.1.4   | MIT                                           |       |
| ✅     | destr                              | 2.0.5   | MIT                                           |       |
| ✅     | dotenv                             | 16.6.1  | BSD-2-Clause                                  |       |
| ✅     | engine.io-client                   | 6.6.3   | MIT                                           |       |
| ✅     | engine.io-parser                   | 5.2.3   | MIT                                           |       |
| ✅     | entities                           | 4.5.0   | BSD-2-Clause                                  |       |
| ✅     | errx                               | 0.1.0   | MIT                                           |       |
| ✅     | escape-string-regexp               | 5.0.0   | MIT                                           |       |
| ✅     | estree-walker                      | 2.0.2   | MIT                                           |       |
| ✅     | eventemitter3                      | 5.0.1   | MIT                                           |       |
| ✅     | exsolve                            | 1.0.7   | MIT                                           |       |
| ✅     | fast-deep-equal                    | 3.1.3   | MIT                                           |       |
| ✅     | fast-diff                          | 1.3.0   | Apache-2.0                                    |       |
| ✅     | fdir                               | 6.5.0   | MIT                                           |       |
| ✅     | fs-minipass                        | 2.1.0   | ISC                                           |       |
| ✅     | fuse.js                            | 7.1.0   | Apache-2.0                                    |       |
| ✅     | giget                              | 1.2.5   | MIT                                           |       |
| ✅     | gridstack                          | 12.3.3  | MIT                                           |       |
| ✅     | handlebars                         | 4.7.8   | MIT                                           |       |
| ✅     | hookable                           | 5.5.3   | MIT                                           |       |
| ✅     | ignore                             | 7.0.5   | MIT                                           |       |
| ✅     | is-what                            | 4.1.16  | MIT                                           |       |
| ✅     | jiti                               | 2.6.0   | MIT                                           |       |
| ✅     | js-tokens                          | 9.0.1   | MIT                                           |       |
| ✅     | js-yaml                            | 4.1.0   | MIT                                           |       |
| ✅     | jwt-decode                         | 4.0.0   | MIT                                           |       |
| ✅     | klona                              | 2.0.6   | MIT                                           |       |
| ✅     | knitwork                           | 1.2.0   | MIT                                           |       |
| ✅     | local-pkg                          | 1.1.2   | MIT                                           |       |
| ✅     | lodash                             | 4.17.21 | MIT                                           |       |
| ✅     | lodash-es                          | 4.17.21 | MIT                                           |       |
| ✅     | lodash.clonedeep                   | 4.5.0   | MIT                                           |       |
| ✅     | lodash.isequal                     | 4.5.0   | MIT                                           |       |
| ✅     | lucide-vue-next                    | 0.513.0 | ISC                                           |       |
| ✅     | magic-string                       | 0.30.19 | MIT                                           |       |
| ✅     | magicast                           | 0.3.5   | MIT                                           |       |
| ✅     | minimist                           | 1.2.8   | MIT                                           |       |
| ✅     | minipass                           | 3.3.6   | ISC                                           |       |
| ✅     | minizlib                           | 2.1.2   | MIT                                           |       |
| ✅     | mitt                               | 3.0.1   | MIT                                           |       |
| ✅     | mkdirp                             | 1.0.4   | MIT                                           |       |
| ✅     | mlly                               | 1.8.0   | MIT                                           |       |
| ✅     | ms                                 | 2.1.3   | MIT                                           |       |
| ✅     | nanoid                             | 3.3.11  | MIT                                           |       |
| ✅     | neo-async                          | 2.6.2   | MIT                                           |       |
| ✅     | node-fetch-native                  | 1.6.7   | MIT                                           |       |
| ✅     | nypm                               | 0.5.4   | MIT                                           |       |
| ✅     | ohash                              | 1.1.6   | MIT                                           |       |
| ✅     | oidc-client-ts                     | 3.3.0   | Apache-2.0                                    |       |
| ✅     | parchment                          | 3.0.0   | BSD-3-Clause                                  |       |
| ✅     | pathe                              | 1.1.2   | MIT                                           |       |
| ✅     | perfect-debounce                   | 1.0.0   | MIT                                           |       |
| ✅     | picocolors                         | 1.1.1   | ISC                                           |       |
| ✅     | picomatch                          | 4.0.3   | MIT                                           |       |
| ✅     | pinia                              | 3.0.3   | MIT                                           |       |
| ✅     | pkg-types                          | 1.3.1   | MIT                                           |       |
| ✅     | postcss                            | 8.5.6   | MIT                                           |       |
| ✅     | primeicons                         | 7.0.0   | MIT                                           |       |
| ✅     | primevue                           | 4.3.6   | MIT                                           |       |
| ✅     | quansync                           | 0.2.11  | MIT                                           |       |
| ✅     | quill                              | 2.0.3   | BSD-3-Clause                                  |       |
| ✅     | quill-delta                        | 5.1.0   | MIT                                           |       |
| ✅     | radix-vue                          | 1.9.17  | MIT                                           |       |
| ✅     | rc9                                | 2.1.2   | MIT                                           |       |
| ✅     | readdirp                           | 4.1.2   | MIT                                           |       |
| ✅     | rfdc                               | 1.4.1   | MIT                                           |       |
| ✅     | scule                              | 1.3.0   | MIT                                           |       |
| ✅     | semver                             | 7.7.2   | ISC                                           |       |
| ✅     | socket.io-client                   | 4.8.1   | MIT                                           |       |
| ✅     | socket.io-parser                   | 4.2.4   | MIT                                           |       |
| ✅     | source-map                         | 0.6.1   | BSD-3-Clause                                  |       |
| ✅     | source-map-js                      | 1.2.1   | BSD-3-Clause                                  |       |
| ✅     | speakingurl                        | 14.0.1  | BSD                                           |       |
| ✅     | std-env                            | 3.9.0   | MIT                                           |       |
| ✅     | strip-literal                      | 3.1.0   | MIT                                           |       |
| ✅     | superjson                          | 2.2.2   | MIT                                           |       |
| ✅     | tailwind-merge                     | 3.3.1   | MIT                                           |       |
| ✅     | tar                                | 6.2.1   | ISC                                           |       |
| ✅     | tinyexec                           | 0.3.2   | MIT                                           |       |
| ✅     | tinyglobby                         | 0.2.15  | MIT                                           |       |
| ✅     | tslib                              | 2.8.1   | 0BSD                                          |       |
| ✅     | typescript                         | 5.9.2   | Apache-2.0                                    |       |
| ✅     | ufo                                | 1.6.1   | MIT                                           |       |
| ✅     | uglify-js                          | 3.19.3  | BSD-2-Clause                                  |       |
| ✅     | unctx                              | 2.4.1   | MIT                                           |       |
| ✅     | unimport                           | 5.4.0   | MIT                                           |       |
| ✅     | unplugin                           | 2.3.10  | MIT                                           |       |
| ✅     | unplugin-utils                     | 0.3.0   | MIT                                           |       |
| ✅     | untyped                            | 2.0.0   | MIT                                           |       |
| ✅     | uuid                               | 11.1.0  | MIT                                           |       |
| ✅     | vue                                | 3.5.17  | MIT                                           |       |
| ✅     | vue-demi                           | 0.14.10 | MIT                                           |       |
| ✅     | vue-router                         | 4.5.1   | MIT                                           |       |
| ✅     | vue3-apexcharts                    | 1.8.0   | MIT                                           |       |
| ✅     | webpack-virtual-modules            | 0.6.2   | MIT                                           |       |
| ✅     | wordwrap                           | 1.0.0   | MIT                                           |       |
| ✅     | ws                                 | 8.17.1  | MIT                                           |       |
| ✅     | xmlhttprequest-ssl                 | 2.1.2   | MIT                                           |       |
| ✅     | yallist                            | 4.0.0   | ISC                                           |       |

## Docker Images

### External Docker Service Licenses

| Status | Service                         | Image                                                                       | License            | Notes                                                             |
| ------ | ------------------------------- | --------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------------------- |
| ⚠️     | open-webui                      | `ghcr.io/bbvch-ai/aihub-core/open-webui:v0.6.41`                            | BSD-3-Clause       | Permissive with required branding retention                       |
| ✅     | oauth2-proxy                    | `ghcr.io/bbvch-ai/bbvch-ai/oauth2-proxy:latest`                             | MIT                | Permissive license                                                |
| ✅     | llama.cpp                       | `ghcr.io/bbvch-ai/aihub-core/llama.cpp:server-cuda-b7003`                   | MIT                | Permissive license                                                |
| ✅     | milvus                          | `ghcr.io/bbvch-ai/aihub-core/milvus:v2.5.15`                                | Apache-2.0         | Permissive license                                                |
| ✅     | minimal-notebook                | `ghcr.io/bbvch-ai/aihub-core/minimal-notebook:notebook-7.0.6`               | BSD-3-Clause       | Jupyter base image                                                |
| ✅     | pgvector                        | `ghcr.io/bbvch-ai/aihub-core/pgvector:pg17`                                 | PostgreSQL License | BSD-style permissive license                                      |
| ✅     | presidio-analyzer               | `ghcr.io/bbvch-ai/aihub-core/presidio-analyzer:2.2.359`                     | MIT                | Permissive license                                                |
| ✅     | docling-serve-cpu               | `ghcr.io/bbvch-ai/aihub-core/docling-serve-cpu:v1.8.0`                      | MIT                | Permissive license                                                |
| ✅     | nats                            | `ghcr.io/bbvch-ai/aihub-core/nats:2.11.4`                                   | Apache-2.0         | Permissive license                                                |
| ✅     | vllm-openai                     | `ghcr.io/bbvch-ai/aihub-core/vllm-openai:v0.11.0`                           | Apache-2.0         | Permissive license                                                |
| ✅     | playwright                      | `ghcr.io/bbvch-ai/aihub-core/playwright:v1.54.1-jammy`                      | Apache-2.0         | Permissive license                                                |
| ✅     | postgres-documentdb             | `ghcr.io/bbvch-ai/aihub-core/postgres-documentdb:17.0.106.0-ferretdb-2.5.0` | Apache-2.0         | Permissive licenses                                               |
| ✅     | traefik                         | `ghcr.io/bbvch-ai/aihub-core/traefik:v3.6.2`                                | Apache-2.0         | Permissive license                                                |
| ✅     | valkey                          | `ghcr.io/bbvch-ai/aihub-core/valkey:8.0.5`                                  | BSD-3-Clause       | Redis-compatible, standard BSD-3-Clause license                   |
| ✅     | postgres                        | `ghcr.io/bbvch-ai/aihub-core/postgres:17`                                   | PostgreSQL License | BSD-style permissive license                                      |
| ✅     | dagster                         | `ghcr.io/bbvch-ai/aihub-core/dagster:latest`                                | Apache-2.0         | Permissive license                                                |
| ✅     | attu                            | `ghcr.io/bbvch-ai/aihub-core/attu:v2.5.12`                                  | Apache-2.0         | Permissive license                                                |
| ✅     | presidio-anonymizer             | `ghcr.io/bbvch-ai/aihub-core/presidio-anonymizer:2.2.359`                   | MIT                | Permissive license                                                |
| ✅     | speaches                        | `ghcr.io/bbvch-ai/aihub-core/speaches:0.8.3-cuda-12.6.3`                    | MIT                | Permissive license                                                |
| ✅     | etcd                            | `ghcr.io/bbvch-ai/aihub-core/etcd:v3.5.16`                                  | Apache-2.0         | Permissive license                                                |
| ✅     | llama.cpp                       | `ghcr.io/bbvch-ai/aihub-core/llama.cpp:server-b7003`                        | MIT                | Permissive license                                                |
| ✅     | litellm                         | `ghcr.io/bbvch-ai/aihub-core/litellm:v1.79.1-stable`                        | MIT                | Permissive license                                                |
| ✅     | ferretdb                        | `ghcr.io/bbvch-ai/aihub-core/ferretdb:2.5.0`                                | Apache-2.0         | Permissive license                                                |
| ✅     | seaweedfs                       | `ghcr.io/bbvch-ai/aihub-core/seaweedfs:3.97`                                | Apache-2.0         | Permissive license                                                |
| ✅     | speaches                        | `ghcr.io/bbvch-ai/aihub-core/speaches:0.8.3-cpu`                            | MIT                | Permissive license                                                |
| ✅     | pgbouncer                       | `ghcr.io/bbvch-ai/aihub-core/pgbouncer:v1.24.1-p1`                          | ISC                | Based on edoburu/pgbouncer (MIT wrapper); permissive licenses     |
| ✅     | aws-cli-alpine                  | `ghcr.io/bbvch-ai/aihub-core/aws-cli-alpine:3.22.1`                         | Apache-2.0         | Permissive license                                                |
| ⚠️     | phoenix                         | `ghcr.io/bbvch-ai/aihub-core/phoenix:version-10.0.4`                        | ELv2               | Source-available; cannot offer as a service, internal use allowed |
| ✅     | dagster                         | `ghcr.io/bbvch-ai/aihub-core/dagster:nightly`                               | Apache-2.0         | Permissive license                                                |
| ✅     | opentelemetry-collector-contrib | `otel/opentelemetry-collector-contrib:latest`                               | Apache-2.0         | Permissive license                                                |

### Internal Docker Images (Our Code)

The following are our own services and inherit the license we choose:

- rag_agent (`ghcr.io/bbvch-ai/aihub-core/rag_agent:nightly`)
- web (`ghcr.io/bbvch-ai/aihub-core/web:latest`)
- rag_agent (`ghcr.io/bbvch-ai/aihub-core/rag_agent:latest`)
- web (`ghcr.io/bbvch-ai/aihub-core/web:nightly`)
- llm_wrapping_agent (`ghcr.io/bbvch-ai/aihub-core/llm_wrapping_agent:nightly`)
- default_rag_pipeline (`ghcr.io/bbvch-ai/aihub-core/default_rag_pipeline:nightly`)
- llm_wrapping_agent (`ghcr.io/bbvch-ai/aihub-core/llm_wrapping_agent:latest`)
- api (`ghcr.io/bbvch-ai/aihub-core/api:latest`)
- default_rag_pipeline (`ghcr.io/bbvch-ai/aihub-core/default_rag_pipeline:latest`)
- bot (`ghcr.io/bbvch-ai/aihub-core/bot:latest`)
- api (`ghcr.io/bbvch-ai/aihub-core/api:nightly`)
- bot (`ghcr.io/bbvch-ai/aihub-core/bot:nightly`)
