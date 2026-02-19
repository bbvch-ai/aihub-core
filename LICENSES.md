# License Report

Generated on: 19.02.2026

This document contains license information for all dependencies across the monorepo:

- Python packages (Poetry): **1626 packages**
- Node.js packages (pnpm): **694 packages**
- External Docker images: **32 images**

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
| ✅     | asttokens                                    | 3.0.1             | Apache 2.0                                        |       |
| ✅     | multidict                                    | 6.7.0             | Apache License 2.0                                |       |
| ✅     | neo4j-graphrag                               | 1.12.0            | Apache-2.0 (override)                             |       |
| ✅     | aiosignal                                    | 1.4.0             | Apache Software License                           |       |
| ✅     | distro                                       | 1.9.0             | Apache Software License                           |       |
| ✅     | flatbuffers                                  | 25.12.19          | Apache Software License                           |       |
| ✅     | googleapis-common-protos                     | 1.72.0            | Apache Software License                           |       |
| ✅     | grpcio                                       | 1.76.0            | Apache Software License                           |       |
| ✅     | huggingface-hub                              | 0.36.0            | Apache Software License                           |       |
| ✅     | magika                                       | 0.6.3             | Apache Software License                           |       |
| ✅     | motor                                        | 3.7.1             | Apache Software License                           |       |
| ✅     | nats-py                                      | 2.12.0            | Apache Software License                           |       |
| ✅     | nltk                                         | 3.9.2             | Apache Software License                           |       |
| ✅     | openai                                       | 1.109.1           | Apache Software License                           |       |
| ✅     | opentelemetry-instrumentation-milvus         | 0.47.5            | Apache Software License                           |       |
| ✅     | opentelemetry-semantic-conventions-ai        | 0.4.13            | Apache Software License                           |       |
| ✅     | propcache                                    | 0.4.1             | Apache Software License                           |       |
| ✅     | pymilvus                                     | 2.6.6             | Apache Software License                           |       |
| ✅     | pymongo                                      | 4.15.5            | Apache Software License                           |       |
| ✅     | pytest-asyncio                               | 0.24.0            | Apache Software License                           |       |
| ✅     | qdrant-client                                | 1.16.2            | Apache Software License                           |       |
| ✅     | requests                                     | 2.32.5            | Apache Software License                           |       |
| ✅     | requests-toolbelt                            | 1.0.0             | Apache Software License                           |       |
| ✅     | s3transfer                                   | 0.15.0            | Apache Software License                           |       |
| ✅     | safetensors                                  | 0.7.0             | Apache Software License                           |       |
| ✅     | tenacity                                     | 9.1.2             | Apache Software License                           |       |
| ✅     | tokenizers                                   | 0.22.1            | Apache Software License                           |       |
| ✅     | transformers                                 | 4.57.3            | Apache Software License                           |       |
| ✅     | yarl                                         | 1.22.0            | Apache Software License                           |       |
| ✅     | packaging                                    | 25.0              | Apache Software License; BSD License              |       |
| ✅     | python-dateutil                              | 2.9.0.post0       | Apache Software License; BSD License              |       |
| ✅     | sniffio                                      | 1.3.1             | Apache Software License; MIT License              |       |
| ✅     | regex                                        | 2025.11.3         | Apache-2.0 (override)                             |       |
| ✅     | aiohttp                                      | 3.13.3            | Apache-2.0 AND MIT                                |       |
| ✅     | neo4j                                        | 6.1.0             | Apache-2.0 AND Python-2.0                         |       |
| ✅     | cryptography                                 | 46.0.3            | Apache-2.0 OR BSD-3-Clause                        |       |
| ✅     | orjson                                       | 3.11.5            | Apache-2.0 OR MIT                                 |       |
| ✅     | ormsgpack                                    | 1.12.2            | Apache-2.0 OR MIT                                 |       |
| ✅     | aiobotocore                                  | 2.26.0            | Apache-2.0                                        |       |
| ✅     | boto3                                        | 1.41.5            | Apache-2.0                                        |       |
| ✅     | botocore                                     | 1.41.5            | Apache-2.0                                        |       |
| ✅     | coverage                                     | 7.13.1            | Apache-2.0                                        |       |
| ✅     | frozenlist                                   | 1.8.0             | Apache-2.0                                        |       |
| ✅     | hf-xet                                       | 1.2.0             | Apache-2.0 (override)                             |       |
| ✅     | importlib_metadata                           | 8.7.1             | Apache-2.0                                        |       |
| ✅     | mem0ai                                       | 1.0.2             | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation                | 0.1.42            | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation-llama-index    | 4.3.9             | Apache-2.0                                        |       |
| ✅     | openinference-semantic-conventions           | 0.1.25            | Apache-2.0                                        |       |
| ✅     | opentelemetry-api                            | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp                  | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-common     | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc       | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-http       | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-instrumentation                | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-asyncio        | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-botocore       | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-httpx          | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-jinja2         | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-logging        | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-pymongo        | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-redis          | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-requests       | 0.60b1            | Apache-2.0                                        |       |
| ✅     | opentelemetry-propagator-aws-xray            | 1.0.2             | Apache-2.0                                        |       |
| ✅     | opentelemetry-proto                          | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-sdk                            | 1.39.1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-semantic-conventions           | 0.60b1            | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-util-http                      | 0.60b1            | Apache-2.0                                        |       |
| ✅     | types-PyYAML                                 | 6.0.12.20250915   | Apache-2.0 (override)                             |       |
| ✅     | types-networkx                               | 3.6.1.20251220    | Apache-2.0 (override)                             |       |
| ✅     | types-pytz                                   | 2025.2.0.20251108 | Apache-2.0                                        |       |
| ✅     | types-requests                               | 2.32.4.20250913   | Apache-2.0 (override)                             |       |
| ✅     | tzdata                                       | 2025.3            | Apache-2.0                                        |       |
| ✅     | rank-bm25                                    | 0.2.2             | Apache2.0                                         |       |
| ✅     | Jinja2                                       | 3.1.6             | BSD License                                       |       |
| ✅     | Pygments                                     | 2.19.2            | BSD License                                       |       |
| ✅     | adlfs                                        | 2025.8.0          | BSD License                                       |       |
| ✅     | cobble                                       | 0.1.4             | BSD License                                       |       |
| ✅     | colorama                                     | 0.4.6             | BSD License                                       |       |
| ✅     | contourpy                                    | 1.3.3             | BSD License                                       |       |
| ✅     | cycler                                       | 0.12.1            | BSD License                                       |       |
| ✅     | decorator                                    | 5.2.1             | BSD License                                       |       |
| ✅     | fsspec                                       | 2024.12.0         | BSD License                                       |       |
| ✅     | httpx                                        | 0.28.1            | BSD License                                       |       |
| ✅     | ipython_pygments_lexers                      | 1.1.1             | BSD License                                       |       |
| ✅     | isodate                                      | 0.7.2             | BSD License                                       |       |
| ✅     | jsonpatch                                    | 1.33              | BSD License                                       |       |
| ✅     | jsonpointer                                  | 3.0.0             | BSD License                                       |       |
| ✅     | kiwisolver                                   | 1.4.9             | BSD License                                       |       |
| ✅     | lxml                                         | 5.4.0             | BSD License                                       |       |
| ✅     | mammoth                                      | 1.11.0            | BSD License                                       |       |
| ✅     | mpmath                                       | 1.3.0             | BSD License                                       |       |
| ✅     | nest-asyncio                                 | 1.6.0             | BSD License                                       |       |
| ✅     | numpy                                        | 2.3.5             | BSD License                                       |       |
| ✅     | olefile                                      | 0.47              | BSD License                                       |       |
| ✅     | pandas                                       | 2.3.3             | BSD License                                       |       |
| ✅     | pandas-stubs                                 | 2.3.3.251219      | BSD License                                       |       |
| ✅     | prompt_toolkit                               | 3.0.52            | BSD License                                       |       |
| ✅     | pycparser                                    | 2.23              | BSD License                                       |       |
| ✅     | s3fs                                         | 2024.12.0         | BSD License                                       |       |
| ✅     | scipy                                        | 1.16.3            | BSD License                                       |       |
| ✅     | striprtf                                     | 0.0.26            | BSD License                                       |       |
| ✅     | sympy                                        | 1.14.0            | BSD License                                       |       |
| ✅     | traitlets                                    | 5.14.3            | BSD License                                       |       |
| ✅     | uuid_utils                                   | 0.14.0            | BSD License                                       |       |
| ✅     | webencodings                                 | 0.5.1             | BSD License                                       |       |
| ✅     | wrapt                                        | 1.17.3            | BSD License                                       |       |
| ✅     | xlsxwriter                                   | 3.2.9             | BSD License                                       |       |
| ✅     | xxhash                                       | 3.6.0             | BSD License                                       |       |
| ✅     | MarkupSafe                                   | 3.0.3             | BSD-3-Clause                                      |       |
| ✅     | click                                        | 8.3.1             | BSD-3-Clause (override)                           |       |
| ✅     | httpcore                                     | 1.0.9             | BSD-3-Clause                                      |       |
| ✅     | idna                                         | 3.11              | BSD-3-Clause                                      |       |
| ✅     | ipython                                      | 9.8.0             | BSD-3-Clause                                      |       |
| ✅     | joblib                                       | 1.5.3             | BSD-3-Clause                                      |       |
| ✅     | networkx                                     | 3.6.1             | BSD-3-Clause                                      |       |
| ✅     | portalocker                                  | 3.2.0             | BSD-3-Clause                                      |       |
| ✅     | pypdf                                        | 6.5.0             | BSD-3-Clause (override)                           |       |
| ✅     | python-dotenv                                | 1.2.1             | BSD-3-Clause                                      |       |
| ✅     | starlette                                    | 0.50.0            | BSD-3-Clause                                      |       |
| ✅     | zstandard                                    | 0.25.0            | BSD-3-Clause                                      |       |
| ✅     | dnspython                                    | 2.8.0             | ISC License (ISCL)                                |       |
| ✅     | pexpect                                      | 4.9.0             | ISC License (ISCL)                                |       |
| ✅     | ptyprocess                                   | 0.7.0             | ISC License (ISCL)                                |       |
| ✅     | griffe                                       | 1.15.0            | ISC (override)                                    |       |
| ✅     | greenlet                                     | 3.3.0             | MIT AND Python-2.0                                |       |
| ✅     | Deprecated                                   | 1.3.1             | MIT License                                       |       |
| ✅     | Mako                                         | 1.3.10            | MIT License                                       |       |
| ✅     | PyJWT                                        | 2.10.1            | MIT License                                       |       |
| ✅     | PyYAML                                       | 6.0.3             | MIT License                                       |       |
| ✅     | aiosqlite                                    | 0.22.1            | MIT License                                       |       |
| ✅     | annotated-types                              | 0.7.0             | MIT License                                       |       |
| ✅     | azure-ai-documentintelligence                | 1.0.2             | MIT License                                       |       |
| ✅     | azure-core                                   | 1.37.0            | MIT License                                       |       |
| ✅     | azure-datalake-store                         | 0.0.53            | MIT License                                       |       |
| ✅     | azure-storage-blob                           | 12.27.1           | MIT License                                       |       |
| ✅     | azure-storage-file-datalake                  | 12.22.0           | MIT License                                       |       |
| ✅     | backoff                                      | 2.2.1             | MIT License                                       |       |
| ✅     | beautifulsoup4                               | 4.14.3            | MIT License                                       |       |
| ✅     | black                                        | 24.10.0           | MIT License                                       |       |
| ✅     | cachetools                                   | 5.5.2             | MIT License                                       |       |
| ✅     | cohere                                       | 5.20.1            | MIT License                                       |       |
| ✅     | coloredlogs                                  | 15.0.1            | MIT License                                       |       |
| ✅     | colorlog                                     | 6.10.1            | MIT License                                       |       |
| ✅     | dataclasses-json                             | 0.6.7             | MIT License                                       |       |
| ✅     | et_xmlfile                                   | 2.0.0             | MIT License                                       |       |
| ✅     | executing                                    | 2.2.1             | MIT License                                       |       |
| ✅     | filetype                                     | 1.2.0             | MIT License                                       |       |
| ✅     | h11                                          | 0.16.0            | MIT License                                       |       |
| ✅     | h2                                           | 4.3.0             | MIT License                                       |       |
| ✅     | hpack                                        | 4.1.0             | MIT License                                       |       |
| ✅     | html5lib                                     | 1.1               | MIT License                                       |       |
| ✅     | humanfriendly                                | 10.0              | MIT License                                       |       |
| ✅     | hyperframe                                   | 6.1.0             | MIT License                                       |       |
| ✅     | jedi                                         | 0.19.2            | MIT License                                       |       |
| ✅     | jiter                                        | 0.12.0            | MIT License                                       |       |
| ✅     | jmespath                                     | 1.0.1             | MIT License                                       |       |
| ✅     | json_repair                                  | 0.44.1            | MIT License                                       |       |
| ✅     | langfuse                                     | 3.14.1            | MIT License                                       |       |
| ✅     | librt                                        | 0.7.7             | MIT License                                       |       |
| ✅     | markdownify                                  | 1.2.2             | MIT License                                       |       |
| ✅     | marshmallow                                  | 3.26.2            | MIT License                                       |       |
| ✅     | memgraph-toolbox                             | 0.1.9             | MIT License                                       |       |
| ✅     | mongoengine                                  | 0.29.1            | MIT License                                       |       |
| ✅     | msal                                         | 1.34.0            | MIT License                                       |       |
| ✅     | msal-extensions                              | 1.3.1             | MIT License                                       |       |
| ✅     | mypy                                         | 1.19.1            | MIT License                                       |       |
| ✅     | onnxruntime                                  | 1.20.1            | MIT License                                       |       |
| ✅     | openpyxl                                     | 3.1.5             | MIT License                                       |       |
| ✅     | parse                                        | 1.20.2            | MIT License                                       |       |
| ✅     | parso                                        | 0.8.5             | MIT License                                       |       |
| ✅     | pluggy                                       | 1.6.0             | MIT License                                       |       |
| ✅     | posthog                                      | 7.6.0             | MIT License                                       |       |
| ✅     | pure_eval                                    | 0.2.3             | MIT License                                       |       |
| ✅     | pytest                                       | 8.4.2             | MIT License                                       |       |
| ✅     | pytest-bdd                                   | 8.1.0             | MIT License                                       |       |
| ✅     | pytest-mock                                  | 3.15.1            | MIT License                                       |       |
| ✅     | python-i18n                                  | 0.3.9             | MIT License                                       |       |
| ✅     | python-pptx                                  | 1.0.2             | MIT License                                       |       |
| ✅     | pytz                                         | 2025.2            | MIT License                                       |       |
| ✅     | redis                                        | 5.3.1             | MIT License                                       |       |
| ✅     | ruff                                         | 0.8.6             | MIT License                                       |       |
| ✅     | six                                          | 1.17.0            | MIT License                                       |       |
| ✅     | stack-data                                   | 0.6.3             | MIT License                                       |       |
| ✅     | tabulate                                     | 0.9.0             | MIT License                                       |       |
| ✅     | toml-sort                                    | 0.24.3            | MIT License                                       |       |
| ✅     | tomlkit                                      | 0.13.3            | MIT License                                       |       |
| ✅     | types-awscrt                                 | 0.31.1            | MIT License                                       |       |
| ✅     | typing-inspect                               | 0.9.0             | MIT License                                       |       |
| ✅     | tqdm                                         | 4.67.1            | MIT License; Mozilla Public License 2.0 (MPL 2.0) |       |
| ✅     | tiktoken                                     | 0.12.0            | MIT (override)                                    |       |
| ✅     | SQLAlchemy                                   | 2.0.45            | MIT                                               |       |
| ✅     | aioitertools                                 | 0.13.0            | MIT                                               |       |
| ✅     | annotated-doc                                | 0.0.4             | MIT                                               |       |
| ✅     | anyio                                        | 4.12.0            | MIT (override)                                    |       |
| ✅     | attrs                                        | 25.4.0            | MIT (override)                                    |       |
| ✅     | azure-identity                               | 1.25.1            | MIT                                               |       |
| ✅     | banks                                        | 2.2.0             | BSD-3-Clause (override)                           |       |
| ✅     | boto3-stubs                                  | 1.42.35           | MIT                                               |       |
| ✅     | botocore-stubs                               | 1.42.35           | MIT                                               |       |
| ✅     | cffi                                         | 2.0.0             | MIT                                               |       |
| ✅     | charset-normalizer                           | 3.4.4             | MIT                                               |       |
| ✅     | fastapi                                      | 0.128.0           | MIT                                               |       |
| ✅     | fastavro                                     | 1.12.1            | MIT                                               |       |
| ✅     | fonttools                                    | 4.61.1            | MIT                                               |       |
| ✅     | gherkin-official                             | 29.0.0            | MIT                                               |       |
| ✅     | iniconfig                                    | 2.3.0             | MIT                                               |       |
| ✅     | kuzu                                         | 0.11.3            | MIT                                               |       |
| ✅     | langchain                                    | 1.2.7             | MIT                                               |       |
| ✅     | langchain-aws                                | 1.1.0             | MIT                                               |       |
| ✅     | langchain-classic                            | 1.0.1             | MIT                                               |       |
| ✅     | langchain-core                               | 1.2.7             | MIT                                               |       |
| ✅     | langchain-memgraph                           | 0.1.12            | MIT                                               |       |
| ✅     | langchain-neo4j                              | 0.8.0             | MIT                                               |       |
| ✅     | langchain-text-splitters                     | 1.1.0             | MIT                                               |       |
| ✅     | langgraph                                    | 1.0.7             | MIT                                               |       |
| ✅     | langgraph-checkpoint                         | 4.0.0             | MIT                                               |       |
| ✅     | langgraph-prebuilt                           | 1.0.7             | MIT                                               |       |
| ✅     | langgraph-sdk                                | 0.3.3             | MIT                                               |       |
| ✅     | langsmith                                    | 0.6.5             | MIT                                               |       |
| ✅     | llama-index-core                             | 0.14.12           | MIT (override)                                    |       |
| ✅     | llama-index-embeddings-openai                | 0.5.1             | MIT                                               |       |
| ✅     | llama-index-embeddings-openai-like           | 0.2.2             | MIT (override)                                    |       |
| ✅     | llama-index-instrumentation                  | 0.4.2             | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai                      | 0.6.12            | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai-like                 | 0.5.3             | MIT (override)                                    |       |
| ✅     | llama-index-postprocessor-cohere-rerank      | 0.5.1             | MIT                                               |       |
| ✅     | llama-index-readers-file                     | 0.5.6             | MIT (override)                                    |       |
| ✅     | llama-index-storage-docstore-mongodb         | 0.4.1             | MIT                                               |       |
| ✅     | llama-index-storage-kvstore-mongodb          | 0.4.1             | MIT                                               |       |
| ✅     | llama-index-vector-stores-milvus             | 0.9.4             | MIT (override)                                    |       |
| ✅     | llama-index-workflows                        | 2.11.6            | MIT (override)                                    |       |
| ✅     | markitdown                                   | 0.1.4             | MIT                                               |       |
| ✅     | mypy-boto3-s3                                | 1.42.21           | MIT                                               |       |
| ✅     | mypy_extensions                              | 1.1.0             | MIT (override)                                    |       |
| ✅     | parse_type                                   | 0.6.6             | MIT (override)                                    |       |
| ✅     | platformdirs                                 | 4.5.1             | MIT                                               |       |
| ✅     | pydantic                                     | 2.12.5            | MIT                                               |       |
| ✅     | pydantic-settings                            | 2.12.0            | MIT                                               |       |
| ✅     | pydantic_core                                | 2.41.5            | MIT                                               |       |
| ✅     | pyparsing                                    | 3.3.1             | MIT                                               |       |
| ✅     | pytest-cov                                   | 6.3.0             | MIT                                               |       |
| ✅     | soupsieve                                    | 2.8.1             | MIT                                               |       |
| ✅     | tokenize_rt                                  | 6.2.0             | MIT                                               |       |
| ✅     | types-s3transfer                             | 0.16.0            | MIT                                               |       |
| ✅     | typing-inspection                            | 0.4.2             | MIT (override)                                    |       |
| ✅     | urllib3                                      | 2.6.2             | MIT (override)                                    |       |
| ✅     | zipp                                         | 3.23.0            | MIT (override)                                    |       |
| ✅     | pillow                                       | 12.1.0            | MIT-CMU (override)                                |       |
| ✅     | certifi                                      | 2026.1.4          | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | pathspec                                     | 0.12.1            | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | typing_extensions                            | 4.15.0            | PSF-2.0 (override)                                |       |
| ✅     | aiohappyeyeballs                             | 2.6.1             | Python Software Foundation License                |       |
| ✅     | defusedxml                                   | 0.7.1             | Python Software Foundation License                |       |
| ✅     | matplotlib                                   | 3.10.8            | Python Software Foundation License                |       |
| ✅     | matplotlib-inline                            | 0.2.1             | BSD-3-Clause (override)                           |       |
| ✅     | filelock                                     | 3.20.2            | Unlicense                                         |       |

### aihub_api

| Status | Package                                          | Version               | License                                                      | Notes |
| ------ | ------------------------------------------------ | --------------------- | ------------------------------------------------------------ | ----- |
| ✅     | protobuf                                         | 5.29.5                | 3-Clause BSD License                                         |       |
| ✅     | dirtyjson                                        | 1.0.8                 | Academic Free License (AFL); MIT License                     |       |
| ✅     | asttokens                                        | 3.0.0                 | Apache 2.0                                                   |       |
| ✅     | multidict                                        | 6.7.0                 | Apache License 2.0                                           |       |
| ✅     | neo4j-graphrag                                   | 1.12.0                | Apache-2.0 (override)                                        |       |
| ✅     | aiosignal                                        | 1.4.0                 | Apache Software License                                      |       |
| ✅     | distro                                           | 1.9.0                 | Apache Software License                                      |       |
| ✅     | flatbuffers                                      | 25.12.19              | Apache Software License                                      |       |
| ✅     | googleapis-common-protos                         | 1.71.0                | Apache Software License                                      |       |
| ✅     | grpcio                                           | 1.76.0                | Apache Software License                                      |       |
| ✅     | huggingface-hub                                  | 0.36.0                | Apache Software License                                      |       |
| ✅     | importlib_metadata                               | 8.7.0                 | Apache Software License                                      |       |
| ✅     | jsonschema-path                                  | 0.3.4                 | Apache Software License                                      |       |
| ✅     | magika                                           | 0.6.3                 | Apache Software License                                      |       |
| ✅     | motor                                            | 3.7.1                 | Apache Software License                                      |       |
| ✅     | nats-py                                          | 2.12.0                | Apache Software License                                      |       |
| ✅     | nltk                                             | 3.9.2                 | Apache Software License                                      |       |
| ✅     | openai                                           | 1.109.1               | Apache Software License                                      |       |
| ✅     | openapi-spec-validator                           | 0.7.2                 | Apache Software License                                      |       |
| ✅     | opentelemetry-instrumentation-milvus             | 0.47.5                | Apache Software License                                      |       |
| ✅     | opentelemetry-semantic-conventions-ai            | 0.4.13                | Apache Software License                                      |       |
| ✅     | pathable                                         | 0.4.4                 | Apache Software License                                      |       |
| ✅     | propcache                                        | 0.4.1                 | Apache Software License                                      |       |
| ✅     | pymilvus                                         | 2.6.3                 | Apache Software License                                      |       |
| ✅     | pymongo                                          | 4.15.3                | Apache Software License                                      |       |
| ✅     | pytest-asyncio                                   | 0.24.0                | Apache Software License                                      |       |
| ✅     | qdrant-client                                    | 1.16.2                | Apache Software License                                      |       |
| ✅     | requests                                         | 2.32.5                | Apache Software License                                      |       |
| ✅     | requests-toolbelt                                | 1.0.0                 | Apache Software License                                      |       |
| ✅     | s3transfer                                       | 0.15.0                | Apache Software License                                      |       |
| ✅     | safetensors                                      | 0.6.2                 | Apache Software License                                      |       |
| ✅     | tenacity                                         | 9.1.2                 | Apache Software License                                      |       |
| ✅     | tokenizers                                       | 0.22.1                | Apache Software License                                      |       |
| ✅     | transformers                                     | 4.57.3                | Apache Software License                                      |       |
| ✅     | tzdata                                           | 2025.2                | Apache Software License                                      |       |
| ✅     | yarl                                             | 1.22.0                | Apache Software License                                      |       |
| ✅     | cryptography                                     | 44.0.3                | Apache Software License; BSD License                         |       |
| ✅     | packaging                                        | 25.0                  | Apache Software License; BSD License                         |       |
| ✅     | python-dateutil                                  | 2.9.0.post0           | Apache Software License; BSD License                         |       |
| ✅     | sniffio                                          | 1.3.1                 | Apache Software License; MIT License                         |       |
| ✅     | uvloop                                           | 0.22.1                | Apache Software License; MIT License                         |       |
| ✅     | regex                                            | 2025.11.3             | Apache-2.0 (override)                                        |       |
| ✅     | aiohttp                                          | 3.13.2                | Apache-2.0 AND MIT                                           |       |
| ✅     | neo4j                                            | 6.1.0                 | Apache-2.0 AND Python-2.0                                    |       |
| ✅     | orjson                                           | 3.11.4                | Apache-2.0 OR MIT                                            |       |
| ✅     | ormsgpack                                        | 1.12.2                | Apache-2.0 OR MIT                                            |       |
| ✅     | aiobotocore                                      | 2.26.0                | Apache-2.0                                                   |       |
| ✅     | boto3                                            | 1.41.5                | Apache-2.0                                                   |       |
| ✅     | botocore                                         | 1.41.5                | Apache-2.0                                                   |       |
| ✅     | coverage                                         | 7.11.0                | Apache-2.0                                                   |       |
| ✅     | cyclopts                                         | 4.2.1                 | Apache-2.0                                                   |       |
| ✅     | fastmcp                                          | 2.12.5                | Apache-2.0                                                   |       |
| ✅     | frozenlist                                       | 1.8.0                 | Apache-2.0                                                   |       |
| ✅     | hf-xet                                           | 1.2.0                 | Apache-2.0 (override)                                        |       |
| ✅     | mem0ai                                           | 1.0.2                 | Apache-2.0                                                   |       |
| ✅     | openinference-instrumentation                    | 0.1.42                | Apache-2.0                                                   |       |
| ✅     | openinference-instrumentation-llama-index        | 4.3.8                 | Apache-2.0                                                   |       |
| ✅     | openinference-semantic-conventions               | 0.1.25                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-api                                | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-exporter-otlp                      | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-exporter-otlp-proto-common         | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc           | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-exporter-otlp-proto-http           | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-instrumentation                    | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client     | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-asgi               | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-asyncio            | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-botocore           | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-fastapi            | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-httpx              | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-jinja2             | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-logging            | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-pymongo            | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-redis              | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-instrumentation-requests           | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | opentelemetry-propagator-aws-xray                | 1.0.2                 | Apache-2.0                                                   |       |
| ✅     | opentelemetry-proto                              | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-sdk                                | 1.39.1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-semantic-conventions               | 0.60b1                | Apache-2.0 (override)                                        |       |
| ✅     | opentelemetry-util-http                          | 0.60b1                | Apache-2.0                                                   |       |
| ✅     | python-multipart                                 | 0.0.20                | Apache-2.0                                                   |       |
| ✅     | types-PyYAML                                     | 6.0.12.20250915       | Apache-2.0 (override)                                        |       |
| ✅     | types-requests                                   | 2.32.4.20250913       | Apache-2.0 (override)                                        |       |
| ✅     | rank-bm25                                        | 0.2.2                 | Apache2.0                                                    |       |
| ✅     | Authlib                                          | 1.6.5                 | BSD License                                                  |       |
| ✅     | Jinja2                                           | 3.1.6                 | BSD License                                                  |       |
| ✅     | Pygments                                         | 2.19.2                | BSD License                                                  |       |
| ✅     | Werkzeug                                         | 3.1.1                 | BSD License                                                  |       |
| ✅     | adlfs                                            | 2025.8.0              | BSD License                                                  |       |
| ✅     | asgiref                                          | 3.10.0                | BSD License                                                  |       |
| ✅     | cobble                                           | 0.1.4                 | BSD License                                                  |       |
| ✅     | colorama                                         | 0.4.6                 | BSD License                                                  |       |
| ✅     | decorator                                        | 5.2.1                 | BSD License                                                  |       |
| ✅     | fsspec                                           | 2024.12.0             | BSD License                                                  |       |
| ✅     | httpx                                            | 0.28.1                | BSD License                                                  |       |
| ✅     | ipython_pygments_lexers                          | 1.1.1                 | BSD License                                                  |       |
| ✅     | isodate                                          | 0.7.2                 | BSD License                                                  |       |
| ✅     | joblib                                           | 1.5.2                 | BSD License                                                  |       |
| ✅     | jsonpatch                                        | 1.33                  | BSD License                                                  |       |
| ✅     | jsonpointer                                      | 3.0.0                 | BSD License                                                  |       |
| ✅     | lxml                                             | 5.4.0                 | BSD License                                                  |       |
| ✅     | mammoth                                          | 1.11.0                | BSD License                                                  |       |
| ✅     | mpmath                                           | 1.3.0                 | BSD License                                                  |       |
| ✅     | nest-asyncio                                     | 1.6.0                 | BSD License                                                  |       |
| ✅     | networkx                                         | 3.5                   | BSD License                                                  |       |
| ✅     | numpy                                            | 2.3.4                 | BSD License                                                  |       |
| ✅     | olefile                                          | 0.47                  | BSD License                                                  |       |
| ✅     | openapi-core                                     | 0.19.5                | BSD License                                                  |       |
| ✅     | openapi-schema-validator                         | 0.6.3                 | BSD License                                                  |       |
| ✅     | pandas                                           | 2.2.3                 | BSD License                                                  |       |
| ✅     | prompt_toolkit                                   | 3.0.52                | BSD License                                                  |       |
| ✅     | pycparser                                        | 2.23                  | BSD License                                                  |       |
| ✅     | pyperclip                                        | 1.11.0                | BSD License                                                  |       |
| ✅     | s3fs                                             | 2024.12.0             | BSD License                                                  |       |
| ✅     | scipy                                            | 1.16.3                | BSD License                                                  |       |
| ✅     | striprtf                                         | 0.0.26                | BSD License                                                  |       |
| ✅     | sympy                                            | 1.14.0                | BSD License                                                  |       |
| ✅     | traitlets                                        | 5.14.3                | BSD License                                                  |       |
| ✅     | uuid_utils                                       | 0.14.0                | BSD License                                                  |       |
| ✅     | webencodings                                     | 0.5.1                 | BSD License                                                  |       |
| ✅     | websockets                                       | 15.0.1                | BSD License                                                  |       |
| ✅     | wrapt                                            | 1.17.3                | BSD License                                                  |       |
| ✅     | xlsxwriter                                       | 3.2.9                 | BSD License                                                  |       |
| ✅     | xxhash                                           | 3.6.0                 | BSD License                                                  |       |
| ✅     | docutils                                         | 0.22.2                | BSD License; GNU General Public License (GPL); Public Domain |       |
| ✅     | lazy-object-proxy                                | 1.12.0                | BSD-2-Clause                                                 |       |
| ✅     | MarkupSafe                                       | 3.0.3                 | BSD-3-Clause                                                 |       |
| ✅     | click                                            | 8.3.0                 | BSD-3-Clause (override)                                      |       |
| ✅     | httpcore                                         | 1.0.9                 | BSD-3-Clause                                                 |       |
| ✅     | idna                                             | 3.11                  | BSD-3-Clause                                                 |       |
| ✅     | ipython                                          | 9.7.0                 | BSD-3-Clause                                                 |       |
| ✅     | portalocker                                      | 3.2.0                 | BSD-3-Clause                                                 |       |
| ✅     | pypdf                                            | 6.5.0                 | BSD-3-Clause (override)                                      |       |
| ✅     | python-dotenv                                    | 1.2.1                 | BSD-3-Clause                                                 |       |
| ✅     | sse-starlette                                    | 3.0.3                 | BSD-3-Clause (override)                                      |       |
| ✅     | starlette                                        | 0.46.2                | BSD-3-Clause                                                 |       |
| ✅     | uvicorn                                          | 0.34.3                | BSD-3-Clause                                                 |       |
| ✅     | zstandard                                        | 0.25.0                | BSD-3-Clause                                                 |       |
| ✅     | dnspython                                        | 2.8.0                 | ISC License (ISCL)                                           |       |
| ✅     | pexpect                                          | 4.9.0                 | ISC License (ISCL)                                           |       |
| ✅     | ptyprocess                                       | 0.7.0                 | ISC License (ISCL)                                           |       |
| ✅     | griffe                                           | 1.14.0                | ISC (override)                                               |       |
| ✅     | greenlet                                         | 3.2.4                 | MIT AND Python-2.0                                           |       |
| ✅     | Deprecated                                       | 1.3.1                 | MIT License                                                  |       |
| ✅     | Mako                                             | 1.3.10                | MIT License                                                  |       |
| ✅     | PyJWT                                            | 2.10.1                | MIT License                                                  |       |
| ✅     | PyYAML                                           | 6.0.3                 | MIT License                                                  |       |
| ✅     | aiosqlite                                        | 0.21.0                | MIT License                                                  |       |
| ✅     | annotated-types                                  | 0.7.0                 | MIT License                                                  |       |
| ✅     | azure-ai-documentintelligence                    | 1.0.2                 | MIT License                                                  |       |
| ✅     | azure-common                                     | 1.1.28                | MIT License                                                  |       |
| ✅     | azure-core                                       | 1.36.0                | MIT License                                                  |       |
| ✅     | azure-datalake-store                             | 0.0.53                | MIT License                                                  |       |
| ✅     | azure-mgmt-core                                  | 1.6.0                 | MIT License                                                  |       |
| ✅     | azure-mgmt-cosmosdb                              | 9.8.0                 | MIT License                                                  |       |
| ✅     | azure-mgmt-resource                              | 23.4.0                | MIT License                                                  |       |
| ✅     | azure-storage-blob                               | 12.27.1               | MIT License                                                  |       |
| ✅     | azure-storage-file-datalake                      | 12.22.0               | MIT License                                                  |       |
| ✅     | backoff                                          | 2.2.1                 | MIT License                                                  |       |
| ✅     | beautifulsoup4                                   | 4.14.2                | MIT License                                                  |       |
| ✅     | cachetools                                       | 5.5.2                 | MIT License                                                  |       |
| ✅     | cohere                                           | 5.20.0                | MIT License                                                  |       |
| ✅     | coloredlogs                                      | 15.0.1                | MIT License                                                  |       |
| ✅     | colorlog                                         | 6.10.1                | MIT License                                                  |       |
| ✅     | dataclasses-json                                 | 0.6.7                 | MIT License                                                  |       |
| ✅     | docstring_parser                                 | 0.17.0                | MIT License                                                  |       |
| ✅     | et_xmlfile                                       | 2.0.0                 | MIT License                                                  |       |
| ✅     | exceptiongroup                                   | 1.3.0                 | MIT License                                                  |       |
| ✅     | executing                                        | 2.2.1                 | MIT License                                                  |       |
| ✅     | filetype                                         | 1.2.0                 | MIT License                                                  |       |
| ✅     | gunicorn                                         | 23.0.0                | MIT License                                                  |       |
| ✅     | h11                                              | 0.16.0                | MIT License                                                  |       |
| ✅     | h2                                               | 4.3.0                 | MIT License                                                  |       |
| ✅     | hpack                                            | 4.1.0                 | MIT License                                                  |       |
| ✅     | html5lib                                         | 1.1                   | MIT License                                                  |       |
| ✅     | humanfriendly                                    | 10.0                  | MIT License                                                  |       |
| ✅     | hyperframe                                       | 6.1.0                 | MIT License                                                  |       |
| ✅     | jedi                                             | 0.19.2                | MIT License                                                  |       |
| ✅     | jiter                                            | 0.11.1                | MIT License                                                  |       |
| ✅     | jmespath                                         | 1.0.1                 | MIT License                                                  |       |
| ✅     | json_repair                                      | 0.44.1                | MIT License                                                  |       |
| ✅     | langfuse                                         | 3.14.1                | MIT License                                                  |       |
| ✅     | markdown-it-py                                   | 4.0.0                 | MIT License                                                  |       |
| ✅     | markdownify                                      | 1.2.2                 | MIT License                                                  |       |
| ✅     | marshmallow                                      | 3.26.1                | MIT License                                                  |       |
| ✅     | mcp                                              | 1.16.0                | MIT License                                                  |       |
| ✅     | mdurl                                            | 0.1.2                 | MIT License                                                  |       |
| ✅     | memgraph-toolbox                                 | 0.1.9                 | MIT License                                                  |       |
| ✅     | mongoengine                                      | 0.29.1                | MIT License                                                  |       |
| ✅     | msal                                             | 1.34.0                | MIT License                                                  |       |
| ✅     | msal-extensions                                  | 1.3.1                 | MIT License                                                  |       |
| ✅     | mypy                                             | 1.18.2                | MIT License                                                  |       |
| ✅     | onnxruntime                                      | 1.20.1                | MIT License                                                  |       |
| ✅     | openapi-pydantic                                 | 0.5.1                 | MIT License                                                  |       |
| ✅     | openpyxl                                         | 3.1.5                 | MIT License                                                  |       |
| ✅     | parse                                            | 1.20.2                | MIT License                                                  |       |
| ✅     | parso                                            | 0.8.5                 | MIT License                                                  |       |
| ✅     | pluggy                                           | 1.6.0                 | MIT License                                                  |       |
| ✅     | posthog                                          | 7.6.0                 | MIT License                                                  |       |
| ✅     | pure_eval                                        | 0.2.3                 | MIT License                                                  |       |
| ✅     | pydub                                            | 0.25.1                | MIT License                                                  |       |
| ✅     | pytest                                           | 8.4.2                 | MIT License                                                  |       |
| ✅     | pytest-bdd                                       | 8.1.0                 | MIT License                                                  |       |
| ✅     | pytest-mock                                      | 3.15.1                | MIT License                                                  |       |
| ✅     | python-i18n                                      | 0.3.9                 | MIT License                                                  |       |
| ✅     | python-pptx                                      | 1.0.2                 | MIT License                                                  |       |
| ✅     | pytokens                                         | 0.3.0                 | MIT License                                                  |       |
| ✅     | pytz                                             | 2025.2                | MIT License                                                  |       |
| ✅     | redis                                            | 5.3.1                 | MIT License                                                  |       |
| ✅     | rfc3339-validator                                | 0.1.4                 | MIT License                                                  |       |
| ✅     | rich                                             | 14.2.0                | MIT License                                                  |       |
| ✅     | ruff                                             | 0.8.6                 | MIT License                                                  |       |
| ✅     | six                                              | 1.17.0                | MIT License                                                  |       |
| ✅     | stack-data                                       | 0.6.3                 | MIT License                                                  |       |
| ✅     | tabulate                                         | 0.9.0                 | MIT License                                                  |       |
| ✅     | toml-sort                                        | 0.24.3                | MIT License                                                  |       |
| ✅     | tomlkit                                          | 0.13.3                | MIT License                                                  |       |
| ✅     | types-awscrt                                     | 0.31.1                | MIT License                                                  |       |
| ✅     | typing-inspect                                   | 0.9.0                 | MIT License                                                  |       |
| ✅     | watchfiles                                       | 1.1.1                 | MIT License                                                  |       |
| ✅     | tqdm                                             | 4.67.1                | MIT License; Mozilla Public License 2.0 (MPL 2.0)            |       |
| ✅     | tiktoken                                         | 0.12.0                | MIT (override)                                               |       |
| ✅     | SQLAlchemy                                       | 2.0.44                | MIT                                                          |       |
| ✅     | aioitertools                                     | 0.13.0                | MIT                                                          |       |
| ✅     | annotated-doc                                    | 0.0.4                 | MIT                                                          |       |
| ✅     | anyio                                            | 4.11.0                | MIT (override)                                               |       |
| ✅     | asgi-lifespan                                    | 2.1.0                 | MIT                                                          |       |
| ✅     | attrs                                            | 25.4.0                | MIT (override)                                               |       |
| ✅     | azure-identity                                   | 1.25.1                | MIT                                                          |       |
| ✅     | banks                                            | 2.2.0                 | BSD-3-Clause (override)                                      |       |
| ✅     | black                                            | 25.9.0                | MIT                                                          |       |
| ✅     | boto3-stubs                                      | 1.42.35               | MIT                                                          |       |
| ✅     | botocore-stubs                                   | 1.42.35               | MIT                                                          |       |
| ✅     | cffi                                             | 2.0.0                 | MIT                                                          |       |
| ✅     | charset-normalizer                               | 3.4.4                 | MIT                                                          |       |
| ✅     | fastapi                                          | 0.128.0               | MIT                                                          |       |
| ✅     | fastavro                                         | 1.12.1                | MIT                                                          |       |
| ✅     | gherkin-official                                 | 29.0.0                | MIT                                                          |       |
| ✅     | httptools                                        | 0.7.1                 | MIT                                                          |       |
| ✅     | httpx-sse                                        | 0.4.0                 | MIT                                                          |       |
| ✅     | iniconfig                                        | 2.3.0                 | MIT                                                          |       |
| ✅     | jambo                                            | 0.1.dev234+g1da93a4d2 | MIT                                                          |       |
| ✅     | jsonschema                                       | 4.25.1                | MIT (override)                                               |       |
| ✅     | jsonschema-specifications                        | 2025.9.1              | MIT (override)                                               |       |
| ✅     | kuzu                                             | 0.11.3                | MIT                                                          |       |
| ✅     | langchain                                        | 1.2.7                 | MIT                                                          |       |
| ✅     | langchain-aws                                    | 1.1.0                 | MIT                                                          |       |
| ✅     | langchain-classic                                | 1.0.1                 | MIT                                                          |       |
| ✅     | langchain-core                                   | 1.2.7                 | MIT                                                          |       |
| ✅     | langchain-memgraph                               | 0.1.12                | MIT                                                          |       |
| ✅     | langchain-neo4j                                  | 0.8.0                 | MIT                                                          |       |
| ✅     | langchain-text-splitters                         | 1.1.0                 | MIT                                                          |       |
| ✅     | langgraph                                        | 1.0.7                 | MIT                                                          |       |
| ✅     | langgraph-checkpoint                             | 4.0.0                 | MIT                                                          |       |
| ✅     | langgraph-prebuilt                               | 1.0.7                 | MIT                                                          |       |
| ✅     | langgraph-sdk                                    | 0.3.3                 | MIT                                                          |       |
| ✅     | langsmith                                        | 0.6.5                 | MIT                                                          |       |
| ✅     | llama-index-core                                 | 0.14.12               | MIT (override)                                               |       |
| ✅     | llama-index-embeddings-openai                    | 0.5.1                 | MIT                                                          |       |
| ✅     | llama-index-embeddings-openai-like               | 0.2.2                 | MIT (override)                                               |       |
| ✅     | llama-index-embeddings-text-embeddings-inference | 0.4.2                 | MIT                                                          |       |
| ✅     | llama-index-instrumentation                      | 0.4.2                 | MIT (override)                                               |       |
| ✅     | llama-index-llms-openai                          | 0.6.12                | MIT (override)                                               |       |
| ✅     | llama-index-llms-openai-like                     | 0.5.3                 | MIT (override)                                               |       |
| ✅     | llama-index-postprocessor-cohere-rerank          | 0.5.1                 | MIT                                                          |       |
| ✅     | llama-index-readers-file                         | 0.5.6                 | MIT (override)                                               |       |
| ✅     | llama-index-storage-docstore-mongodb             | 0.4.1                 | MIT                                                          |       |
| ✅     | llama-index-storage-kvstore-mongodb              | 0.4.1                 | MIT                                                          |       |
| ✅     | llama-index-utils-huggingface                    | 0.4.1                 | MIT                                                          |       |
| ✅     | llama-index-vector-stores-milvus                 | 0.9.4                 | MIT (override)                                               |       |
| ✅     | llama-index-workflows                            | 2.11.6                | MIT (override)                                               |       |
| ✅     | markitdown                                       | 0.1.4                 | MIT                                                          |       |
| ✅     | more-itertools                                   | 10.8.0                | MIT                                                          |       |
| ✅     | mypy-boto3-s3                                    | 1.42.21               | MIT                                                          |       |
| ✅     | mypy_extensions                                  | 1.1.0                 | MIT (override)                                               |       |
| ✅     | parse_type                                       | 0.6.6                 | MIT (override)                                               |       |
| ✅     | platformdirs                                     | 4.5.0                 | MIT                                                          |       |
| ✅     | pydantic                                         | 2.12.4                | MIT                                                          |       |
| ✅     | pydantic-settings                                | 2.11.0                | MIT                                                          |       |
| ✅     | pydantic_core                                    | 2.41.5                | MIT                                                          |       |
| ✅     | pytest-cov                                       | 6.3.0                 | MIT                                                          |       |
| ✅     | referencing                                      | 0.36.2                | MIT (override)                                               |       |
| ✅     | rich-rst                                         | 1.3.2                 | MIT                                                          |       |
| ✅     | rpds-py                                          | 0.28.0                | MIT (override)                                               |       |
| ✅     | soupsieve                                        | 2.8                   | MIT                                                          |       |
| ✅     | stringcase                                       | 1.2.0                 | MIT                                                          |       |
| ✅     | tokenize_rt                                      | 6.2.0                 | MIT                                                          |       |
| ✅     | types-s3transfer                                 | 0.16.0                | MIT                                                          |       |
| ✅     | typing-inspection                                | 0.4.2                 | MIT (override)                                               |       |
| ✅     | urllib3                                          | 2.5.0                 | MIT (override)                                               |       |
| ✅     | zipp                                             | 3.23.0                | MIT (override)                                               |       |
| ✅     | pillow                                           | 12.0.0                | MIT-CMU (override)                                           |       |
| ✅     | certifi                                          | 2025.10.5             | Mozilla Public License 2.0 (MPL 2.0)                         |       |
| ✅     | pathspec                                         | 0.12.1                | Mozilla Public License 2.0 (MPL 2.0)                         |       |
| ✅     | audioop-lts                                      | 0.2.2                 | PSF-2.0 (override)                                           |       |
| ✅     | typing_extensions                                | 4.15.0                | PSF-2.0 (override)                                           |       |
| ✅     | aiohappyeyeballs                                 | 2.6.1                 | Python Software Foundation License                           |       |
| ✅     | defusedxml                                       | 0.7.1                 | Python Software Foundation License                           |       |
| ✅     | email-validator                                  | 2.3.0                 | The Unlicense (Unlicense)                                    |       |
| ✅     | matplotlib-inline                                | 0.2.1                 | BSD-3-Clause (override)                                      |       |
| ✅     | filelock                                         | 3.20.0                | Unlicense                                                    |       |

### aihub_bot

| Status | Package                                      | Version         | License                                           | Notes |
| ------ | -------------------------------------------- | --------------- | ------------------------------------------------- | ----- |
| ✅     | protobuf                                     | 5.29.5          | 3-Clause BSD License                              |       |
| ✅     | dirtyjson                                    | 1.0.8           | Academic Free License (AFL); MIT License          |       |
| ✅     | asttokens                                    | 3.0.1           | Apache 2.0                                        |       |
| ✅     | multidict                                    | 6.7.0           | Apache License 2.0                                |       |
| ✅     | neo4j-graphrag                               | 1.12.0          | Apache-2.0 (override)                             |       |
| ✅     | aiosignal                                    | 1.4.0           | Apache Software License                           |       |
| ✅     | distro                                       | 1.9.0           | Apache Software License                           |       |
| ✅     | flatbuffers                                  | 25.12.19        | Apache Software License                           |       |
| ✅     | googleapis-common-protos                     | 1.72.0          | Apache Software License                           |       |
| ✅     | grpcio                                       | 1.76.0          | Apache Software License                           |       |
| ✅     | huggingface-hub                              | 0.36.0          | Apache Software License                           |       |
| ✅     | importlib_metadata                           | 8.7.0           | Apache Software License                           |       |
| ✅     | magika                                       | 0.6.3           | Apache Software License                           |       |
| ✅     | motor                                        | 3.7.1           | Apache Software License                           |       |
| ✅     | nats-py                                      | 2.12.0          | Apache Software License                           |       |
| ✅     | nltk                                         | 3.9.2           | Apache Software License                           |       |
| ✅     | openai                                       | 1.109.1         | Apache Software License                           |       |
| ✅     | opentelemetry-instrumentation-milvus         | 0.47.5          | Apache Software License                           |       |
| ✅     | opentelemetry-semantic-conventions-ai        | 0.4.13          | Apache Software License                           |       |
| ✅     | propcache                                    | 0.4.1           | Apache Software License                           |       |
| ✅     | pymilvus                                     | 2.6.3           | Apache Software License                           |       |
| ✅     | pymongo                                      | 4.15.4          | Apache Software License                           |       |
| ✅     | pytest-asyncio                               | 0.24.0          | Apache Software License                           |       |
| ✅     | qdrant-client                                | 1.16.2          | Apache Software License                           |       |
| ✅     | requests                                     | 2.32.5          | Apache Software License                           |       |
| ✅     | requests-toolbelt                            | 1.0.0           | Apache Software License                           |       |
| ✅     | s3transfer                                   | 0.15.0          | Apache Software License                           |       |
| ✅     | safetensors                                  | 0.6.2           | Apache Software License                           |       |
| ✅     | tenacity                                     | 9.1.2           | Apache Software License                           |       |
| ✅     | tokenizers                                   | 0.22.1          | Apache Software License                           |       |
| ✅     | transformers                                 | 4.57.3          | Apache Software License                           |       |
| ✅     | tzdata                                       | 2025.2          | Apache Software License                           |       |
| ✅     | yarl                                         | 1.22.0          | Apache Software License                           |       |
| ✅     | cryptography                                 | 44.0.3          | Apache Software License; BSD License              |       |
| ✅     | packaging                                    | 25.0            | Apache Software License; BSD License              |       |
| ✅     | python-dateutil                              | 2.9.0.post0     | Apache Software License; BSD License              |       |
| ✅     | sniffio                                      | 1.3.1           | Apache Software License; MIT License              |       |
| ✅     | regex                                        | 2025.11.3       | Apache-2.0 (override)                             |       |
| ✅     | aiohttp                                      | 3.13.2          | Apache-2.0 AND MIT                                |       |
| ✅     | neo4j                                        | 6.1.0           | Apache-2.0 AND Python-2.0                         |       |
| ✅     | orjson                                       | 3.11.4          | Apache-2.0 OR MIT                                 |       |
| ✅     | ormsgpack                                    | 1.12.2          | Apache-2.0 OR MIT                                 |       |
| ✅     | aiobotocore                                  | 2.26.0          | Apache-2.0                                        |       |
| ✅     | boto3                                        | 1.41.5          | Apache-2.0                                        |       |
| ✅     | botocore                                     | 1.41.5          | Apache-2.0                                        |       |
| ✅     | coverage                                     | 7.11.3          | Apache-2.0                                        |       |
| ✅     | frozenlist                                   | 1.8.0           | Apache-2.0                                        |       |
| ✅     | hf-xet                                       | 1.2.0           | Apache-2.0 (override)                             |       |
| ✅     | mem0ai                                       | 1.0.2           | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation                | 0.1.42          | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation-llama-index    | 4.3.8           | Apache-2.0                                        |       |
| ✅     | openinference-semantic-conventions           | 0.1.25          | Apache-2.0                                        |       |
| ✅     | opentelemetry-api                            | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp                  | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-common     | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc       | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-http       | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-instrumentation                | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-asyncio        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-botocore       | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-httpx          | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-jinja2         | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-logging        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-pymongo        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-redis          | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-requests       | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-propagator-aws-xray            | 1.0.2           | Apache-2.0                                        |       |
| ✅     | opentelemetry-proto                          | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-sdk                            | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-semantic-conventions           | 0.60b1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-util-http                      | 0.60b1          | Apache-2.0                                        |       |
| ✅     | types-PyYAML                                 | 6.0.12.20250915 | Apache-2.0 (override)                             |       |
| ✅     | types-requests                               | 2.32.4.20250913 | Apache-2.0 (override)                             |       |
| ✅     | rank-bm25                                    | 0.2.2           | Apache2.0                                         |       |
| ✅     | Jinja2                                       | 3.1.6           | BSD License                                       |       |
| ✅     | Pygments                                     | 2.19.2          | BSD License                                       |       |
| ✅     | adlfs                                        | 2025.8.0        | BSD License                                       |       |
| ✅     | cobble                                       | 0.1.4           | BSD License                                       |       |
| ✅     | colorama                                     | 0.4.6           | BSD License                                       |       |
| ✅     | decorator                                    | 5.2.1           | BSD License                                       |       |
| ✅     | fsspec                                       | 2024.12.0       | BSD License                                       |       |
| ✅     | httpx                                        | 0.28.1          | BSD License                                       |       |
| ✅     | ipython_pygments_lexers                      | 1.1.1           | BSD License                                       |       |
| ✅     | isodate                                      | 0.7.2           | BSD License                                       |       |
| ✅     | joblib                                       | 1.5.2           | BSD License                                       |       |
| ✅     | jsonpatch                                    | 1.33            | BSD License                                       |       |
| ✅     | jsonpointer                                  | 3.0.0           | BSD License                                       |       |
| ✅     | lxml                                         | 5.4.0           | BSD License                                       |       |
| ✅     | mammoth                                      | 1.11.0          | BSD License                                       |       |
| ✅     | mpmath                                       | 1.3.0           | BSD License                                       |       |
| ✅     | nest-asyncio                                 | 1.6.0           | BSD License                                       |       |
| ✅     | networkx                                     | 3.5             | BSD License                                       |       |
| ✅     | numpy                                        | 2.3.5           | BSD License                                       |       |
| ✅     | olefile                                      | 0.47            | BSD License                                       |       |
| ✅     | pandas                                       | 2.2.3           | BSD License                                       |       |
| ✅     | prompt_toolkit                               | 3.0.52          | BSD License                                       |       |
| ✅     | pycparser                                    | 2.23            | BSD License                                       |       |
| ✅     | requests-oauthlib                            | 2.0.0           | BSD License                                       |       |
| ✅     | s3fs                                         | 2024.12.0       | BSD License                                       |       |
| ✅     | scipy                                        | 1.16.3          | BSD License                                       |       |
| ✅     | striprtf                                     | 0.0.26          | BSD License                                       |       |
| ✅     | sympy                                        | 1.14.0          | BSD License                                       |       |
| ✅     | traitlets                                    | 5.14.3          | BSD License                                       |       |
| ✅     | uuid_utils                                   | 0.14.0          | BSD License                                       |       |
| ✅     | webencodings                                 | 0.5.1           | BSD License                                       |       |
| ✅     | wrapt                                        | 1.17.3          | BSD License                                       |       |
| ✅     | xlsxwriter                                   | 3.2.9           | BSD License                                       |       |
| ✅     | xxhash                                       | 3.6.0           | BSD License                                       |       |
| ✅     | MarkupSafe                                   | 3.0.3           | BSD-3-Clause                                      |       |
| ✅     | click                                        | 8.3.1           | BSD-3-Clause (override)                           |       |
| ✅     | httpcore                                     | 1.0.9           | BSD-3-Clause                                      |       |
| ✅     | idna                                         | 3.11            | BSD-3-Clause                                      |       |
| ✅     | ipython                                      | 9.7.0           | BSD-3-Clause                                      |       |
| ✅     | oauthlib                                     | 3.3.1           | BSD-3-Clause                                      |       |
| ✅     | portalocker                                  | 3.2.0           | BSD-3-Clause                                      |       |
| ✅     | pypdf                                        | 6.5.0           | BSD-3-Clause (override)                           |       |
| ✅     | python-dotenv                                | 1.2.1           | BSD-3-Clause                                      |       |
| ✅     | starlette                                    | 0.46.2          | BSD-3-Clause                                      |       |
| ✅     | uvicorn                                      | 0.34.3          | BSD-3-Clause                                      |       |
| ✅     | zstandard                                    | 0.25.0          | BSD-3-Clause                                      |       |
| ✅     | dnspython                                    | 2.8.0           | ISC License (ISCL)                                |       |
| ✅     | pexpect                                      | 4.9.0           | ISC License (ISCL)                                |       |
| ✅     | ptyprocess                                   | 0.7.0           | ISC License (ISCL)                                |       |
| ✅     | griffe                                       | 1.15.0          | ISC (override)                                    |       |
| ✅     | greenlet                                     | 3.2.4           | MIT AND Python-2.0                                |       |
| ✅     | Deprecated                                   | 1.3.1           | MIT License                                       |       |
| ✅     | Mako                                         | 1.3.10          | MIT License                                       |       |
| ✅     | PyJWT                                        | 2.10.1          | MIT License                                       |       |
| ✅     | PyYAML                                       | 6.0.3           | MIT License                                       |       |
| ✅     | aiosqlite                                    | 0.21.0          | MIT License                                       |       |
| ✅     | annotated-types                              | 0.7.0           | MIT License                                       |       |
| ✅     | azure-ai-documentintelligence                | 1.0.2           | MIT License                                       |       |
| ✅     | azure-common                                 | 1.1.28          | MIT License                                       |       |
| ✅     | azure-core                                   | 1.36.0          | MIT License                                       |       |
| ✅     | azure-datalake-store                         | 0.0.53          | MIT License                                       |       |
| ✅     | azure-mgmt-core                              | 1.6.0           | MIT License                                       |       |
| ✅     | azure-mgmt-resource                          | 23.4.0          | MIT License                                       |       |
| ✅     | azure-storage-blob                           | 12.27.1         | MIT License                                       |       |
| ✅     | azure-storage-file-datalake                  | 12.22.0         | MIT License                                       |       |
| ✅     | backoff                                      | 2.2.1           | MIT License                                       |       |
| ✅     | beautifulsoup4                               | 4.14.2          | MIT License                                       |       |
| ✅     | cachetools                                   | 5.5.2           | MIT License                                       |       |
| ✅     | cohere                                       | 5.20.0          | MIT License                                       |       |
| ✅     | coloredlogs                                  | 15.0.1          | MIT License                                       |       |
| ✅     | colorlog                                     | 6.10.1          | MIT License                                       |       |
| ✅     | dataclasses-json                             | 0.6.7           | MIT License                                       |       |
| ✅     | et_xmlfile                                   | 2.0.0           | MIT License                                       |       |
| ✅     | executing                                    | 2.2.1           | MIT License                                       |       |
| ✅     | filetype                                     | 1.2.0           | MIT License                                       |       |
| ✅     | gunicorn                                     | 23.0.0          | MIT License                                       |       |
| ✅     | h11                                          | 0.16.0          | MIT License                                       |       |
| ✅     | h2                                           | 4.3.0           | MIT License                                       |       |
| ✅     | hpack                                        | 4.1.0           | MIT License                                       |       |
| ✅     | html5lib                                     | 1.1             | MIT License                                       |       |
| ✅     | humanfriendly                                | 10.0            | MIT License                                       |       |
| ✅     | hyperframe                                   | 6.1.0           | MIT License                                       |       |
| ✅     | jedi                                         | 0.19.2          | MIT License                                       |       |
| ✅     | jiter                                        | 0.12.0          | MIT License                                       |       |
| ✅     | jmespath                                     | 1.0.1           | MIT License                                       |       |
| ✅     | json_repair                                  | 0.44.1          | MIT License                                       |       |
| ✅     | langfuse                                     | 3.14.1          | MIT License                                       |       |
| ✅     | markdownify                                  | 1.2.2           | MIT License                                       |       |
| ✅     | marshmallow                                  | 3.26.1          | MIT License                                       |       |
| ✅     | memgraph-toolbox                             | 0.1.9           | MIT License                                       |       |
| ✅     | mongoengine                                  | 0.29.1          | MIT License                                       |       |
| ✅     | msal                                         | 1.34.0          | MIT License                                       |       |
| ✅     | msal-extensions                              | 1.3.1           | MIT License                                       |       |
| ✅     | msrest                                       | 0.7.1           | MIT License                                       |       |
| ✅     | mypy                                         | 1.18.2          | MIT License                                       |       |
| ✅     | onnxruntime                                  | 1.20.1          | MIT License                                       |       |
| ✅     | openpyxl                                     | 3.1.5           | MIT License                                       |       |
| ✅     | parse                                        | 1.20.2          | MIT License                                       |       |
| ✅     | parso                                        | 0.8.5           | MIT License                                       |       |
| ✅     | pluggy                                       | 1.6.0           | MIT License                                       |       |
| ✅     | posthog                                      | 7.6.0           | MIT License                                       |       |
| ✅     | pure_eval                                    | 0.2.3           | MIT License                                       |       |
| ✅     | pytest                                       | 8.4.2           | MIT License                                       |       |
| ✅     | pytest-bdd                                   | 8.1.0           | MIT License                                       |       |
| ✅     | pytest-mock                                  | 3.15.1          | MIT License                                       |       |
| ✅     | python-i18n                                  | 0.3.9           | MIT License                                       |       |
| ✅     | python-pptx                                  | 1.0.2           | MIT License                                       |       |
| ✅     | pytokens                                     | 0.3.0           | MIT License                                       |       |
| ✅     | pytz                                         | 2025.2          | MIT License                                       |       |
| ✅     | redis                                        | 5.3.1           | MIT License                                       |       |
| ✅     | ruff                                         | 0.8.6           | MIT License                                       |       |
| ✅     | six                                          | 1.17.0          | MIT License                                       |       |
| ✅     | stack-data                                   | 0.6.3           | MIT License                                       |       |
| ✅     | tabulate                                     | 0.9.0           | MIT License                                       |       |
| ✅     | toml-sort                                    | 0.24.3          | MIT License                                       |       |
| ✅     | tomlkit                                      | 0.13.3          | MIT License                                       |       |
| ✅     | types-awscrt                                 | 0.31.1          | MIT License                                       |       |
| ✅     | typing-inspect                               | 0.9.0           | MIT License                                       |       |
| ✅     | tqdm                                         | 4.67.1          | MIT License; Mozilla Public License 2.0 (MPL 2.0) |       |
| ✅     | tiktoken                                     | 0.12.0          | MIT (override)                                    |       |
| ✅     | SQLAlchemy                                   | 2.0.44          | MIT                                               |       |
| ✅     | aioitertools                                 | 0.13.0          | MIT                                               |       |
| ✅     | annotated-doc                                | 0.0.4           | MIT                                               |       |
| ✅     | anyio                                        | 4.11.0          | MIT (override)                                    |       |
| ✅     | asgi-lifespan                                | 2.1.0           | MIT                                               |       |
| ✅     | attrs                                        | 25.4.0          | MIT (override)                                    |       |
| ✅     | azure-identity                               | 1.25.1          | MIT                                               |       |
| ✅     | azure-mgmt-cosmosdb                          | 9.9.0           | MIT                                               |       |
| ✅     | banks                                        | 2.2.0           | BSD-3-Clause (override)                           |       |
| ✅     | black                                        | 25.11.0         | MIT                                               |       |
| ✅     | boto3-stubs                                  | 1.42.35         | MIT                                               |       |
| ✅     | botocore-stubs                               | 1.42.35         | MIT                                               |       |
| ✅     | cffi                                         | 2.0.0           | MIT                                               |       |
| ✅     | charset-normalizer                           | 3.4.4           | MIT                                               |       |
| ✅     | fastapi                                      | 0.128.0         | MIT                                               |       |
| ✅     | fastavro                                     | 1.12.1          | MIT                                               |       |
| ✅     | gherkin-official                             | 29.0.0          | MIT                                               |       |
| ✅     | httpx-sse                                    | 0.4.0           | MIT                                               |       |
| ✅     | iniconfig                                    | 2.3.0           | MIT                                               |       |
| ✅     | kuzu                                         | 0.11.3          | MIT                                               |       |
| ✅     | langchain                                    | 1.2.7           | MIT                                               |       |
| ✅     | langchain-aws                                | 1.1.0           | MIT                                               |       |
| ✅     | langchain-classic                            | 1.0.1           | MIT                                               |       |
| ✅     | langchain-core                               | 1.2.7           | MIT                                               |       |
| ✅     | langchain-memgraph                           | 0.1.12          | MIT                                               |       |
| ✅     | langchain-neo4j                              | 0.8.0           | MIT                                               |       |
| ✅     | langchain-text-splitters                     | 1.1.0           | MIT                                               |       |
| ✅     | langgraph                                    | 1.0.7           | MIT                                               |       |
| ✅     | langgraph-checkpoint                         | 4.0.0           | MIT                                               |       |
| ✅     | langgraph-prebuilt                           | 1.0.7           | MIT                                               |       |
| ✅     | langgraph-sdk                                | 0.3.3           | MIT                                               |       |
| ✅     | langsmith                                    | 0.6.5           | MIT                                               |       |
| ✅     | llama-index-core                             | 0.14.12         | MIT (override)                                    |       |
| ✅     | llama-index-embeddings-openai                | 0.5.1           | MIT                                               |       |
| ✅     | llama-index-embeddings-openai-like           | 0.2.2           | MIT (override)                                    |       |
| ✅     | llama-index-instrumentation                  | 0.4.2           | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai                      | 0.6.12          | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai-like                 | 0.5.3           | MIT (override)                                    |       |
| ✅     | llama-index-postprocessor-cohere-rerank      | 0.5.1           | MIT                                               |       |
| ✅     | llama-index-readers-file                     | 0.5.6           | MIT (override)                                    |       |
| ✅     | llama-index-storage-docstore-mongodb         | 0.4.1           | MIT                                               |       |
| ✅     | llama-index-storage-kvstore-mongodb          | 0.4.1           | MIT                                               |       |
| ✅     | llama-index-vector-stores-milvus             | 0.9.4           | MIT (override)                                    |       |
| ✅     | llama-index-workflows                        | 2.11.6          | MIT (override)                                    |       |
| ✅     | markitdown                                   | 0.1.4           | MIT                                               |       |
| ✅     | microsoft-agents-activity                    | 0.5.3           | MIT                                               |       |
| ✅     | microsoft-agents-authentication-msal         | 0.5.3           | MIT                                               |       |
| ✅     | microsoft-agents-hosting-aiohttp             | 0.5.3           | MIT                                               |       |
| ✅     | microsoft-agents-hosting-core                | 0.5.3           | MIT                                               |       |
| ✅     | mypy-boto3-s3                                | 1.42.21         | MIT                                               |       |
| ✅     | mypy_extensions                              | 1.1.0           | MIT (override)                                    |       |
| ✅     | parse_type                                   | 0.6.6           | MIT (override)                                    |       |
| ✅     | platformdirs                                 | 4.5.0           | MIT                                               |       |
| ✅     | pydantic                                     | 2.12.4          | MIT                                               |       |
| ✅     | pydantic-settings                            | 2.12.0          | MIT                                               |       |
| ✅     | pydantic_core                                | 2.41.5          | MIT                                               |       |
| ✅     | pytest-cov                                   | 6.3.0           | MIT                                               |       |
| ✅     | soupsieve                                    | 2.8             | MIT                                               |       |
| ✅     | tokenize_rt                                  | 6.2.0           | MIT                                               |       |
| ✅     | types-s3transfer                             | 0.16.0          | MIT                                               |       |
| ✅     | typing-inspection                            | 0.4.2           | MIT (override)                                    |       |
| ✅     | urllib3                                      | 2.5.0           | MIT (override)                                    |       |
| ✅     | zipp                                         | 3.23.0          | MIT (override)                                    |       |
| ✅     | pillow                                       | 12.0.0          | MIT-CMU (override)                                |       |
| ✅     | certifi                                      | 2025.11.12      | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | pathspec                                     | 0.12.1          | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | typing_extensions                            | 4.15.0          | PSF-2.0 (override)                                |       |
| ✅     | aiohappyeyeballs                             | 2.6.1           | Python Software Foundation License                |       |
| ✅     | defusedxml                                   | 0.7.1           | Python Software Foundation License                |       |
| ✅     | matplotlib-inline                            | 0.2.1           | BSD-3-Clause (override)                           |       |
| ✅     | filelock                                     | 3.20.0          | Unlicense                                         |       |

### aihub_agent

| Status | Package                                      | Version         | License                                           | Notes |
| ------ | -------------------------------------------- | --------------- | ------------------------------------------------- | ----- |
| ✅     | protobuf                                     | 5.29.5          | 3-Clause BSD License                              |       |
| ✅     | dirtyjson                                    | 1.0.8           | Academic Free License (AFL); MIT License          |       |
| ✅     | asttokens                                    | 3.0.0           | Apache 2.0                                        |       |
| ✅     | multidict                                    | 6.7.0           | Apache License 2.0                                |       |
| ✅     | neo4j-graphrag                               | 1.12.0          | Apache-2.0 (override)                             |       |
| ✅     | aiosignal                                    | 1.4.0           | Apache Software License                           |       |
| ✅     | distro                                       | 1.9.0           | Apache Software License                           |       |
| ✅     | flatbuffers                                  | 25.12.19        | Apache Software License                           |       |
| ✅     | googleapis-common-protos                     | 1.71.0          | Apache Software License                           |       |
| ✅     | grpcio                                       | 1.76.0          | Apache Software License                           |       |
| ✅     | huggingface-hub                              | 0.36.0          | Apache Software License                           |       |
| ✅     | importlib_metadata                           | 8.7.0           | Apache Software License                           |       |
| ✅     | magika                                       | 0.6.3           | Apache Software License                           |       |
| ✅     | motor                                        | 3.7.1           | Apache Software License                           |       |
| ✅     | nats-py                                      | 2.12.0          | Apache Software License                           |       |
| ✅     | nltk                                         | 3.9.2           | Apache Software License                           |       |
| ✅     | openai                                       | 1.109.1         | Apache Software License                           |       |
| ✅     | opentelemetry-instrumentation-milvus         | 0.47.5          | Apache Software License                           |       |
| ✅     | opentelemetry-semantic-conventions-ai        | 0.4.13          | Apache Software License                           |       |
| ✅     | propcache                                    | 0.4.1           | Apache Software License                           |       |
| ✅     | pymilvus                                     | 2.6.3           | Apache Software License                           |       |
| ✅     | pymongo                                      | 4.15.3          | Apache Software License                           |       |
| ✅     | pytest-asyncio                               | 0.24.0          | Apache Software License                           |       |
| ✅     | qdrant-client                                | 1.16.2          | Apache Software License                           |       |
| ✅     | requests                                     | 2.32.5          | Apache Software License                           |       |
| ✅     | requests-toolbelt                            | 1.0.0           | Apache Software License                           |       |
| ✅     | s3transfer                                   | 0.15.0          | Apache Software License                           |       |
| ✅     | safetensors                                  | 0.6.2           | Apache Software License                           |       |
| ✅     | tenacity                                     | 9.1.2           | Apache Software License                           |       |
| ✅     | tokenizers                                   | 0.22.1          | Apache Software License                           |       |
| ✅     | transformers                                 | 4.57.3          | Apache Software License                           |       |
| ✅     | tzdata                                       | 2025.2          | Apache Software License                           |       |
| ✅     | yarl                                         | 1.22.0          | Apache Software License                           |       |
| ✅     | packaging                                    | 25.0            | Apache Software License; BSD License              |       |
| ✅     | python-dateutil                              | 2.9.0.post0     | Apache Software License; BSD License              |       |
| ✅     | sniffio                                      | 1.3.1           | Apache Software License; MIT License              |       |
| ✅     | regex                                        | 2025.11.3       | Apache-2.0 (override)                             |       |
| ✅     | aiohttp                                      | 3.13.2          | Apache-2.0 AND MIT                                |       |
| ✅     | neo4j                                        | 6.1.0           | Apache-2.0 AND Python-2.0                         |       |
| ✅     | cryptography                                 | 46.0.3          | Apache-2.0 OR BSD-3-Clause                        |       |
| ✅     | orjson                                       | 3.11.4          | Apache-2.0 OR MIT                                 |       |
| ✅     | ormsgpack                                    | 1.12.2          | Apache-2.0 OR MIT                                 |       |
| ✅     | aiobotocore                                  | 2.26.0          | Apache-2.0                                        |       |
| ✅     | boto3                                        | 1.41.5          | Apache-2.0                                        |       |
| ✅     | botocore                                     | 1.41.5          | Apache-2.0                                        |       |
| ✅     | coverage                                     | 7.11.0          | Apache-2.0                                        |       |
| ✅     | frozenlist                                   | 1.8.0           | Apache-2.0                                        |       |
| ✅     | hf-xet                                       | 1.2.0           | Apache-2.0 (override)                             |       |
| ✅     | mem0ai                                       | 1.0.2           | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation                | 0.1.42          | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation-llama-index    | 4.3.8           | Apache-2.0                                        |       |
| ✅     | openinference-semantic-conventions           | 0.1.25          | Apache-2.0                                        |       |
| ✅     | opentelemetry-api                            | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp                  | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-common     | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc       | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-http       | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-instrumentation                | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-asyncio        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-botocore       | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-httpx          | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-jinja2         | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-logging        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-pymongo        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-redis          | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-requests       | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-propagator-aws-xray            | 1.0.2           | Apache-2.0                                        |       |
| ✅     | opentelemetry-proto                          | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-sdk                            | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-semantic-conventions           | 0.60b1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-util-http                      | 0.60b1          | Apache-2.0                                        |       |
| ✅     | types-PyYAML                                 | 6.0.12.20250915 | Apache-2.0 (override)                             |       |
| ✅     | types-requests                               | 2.32.4.20250913 | Apache-2.0 (override)                             |       |
| ✅     | rank-bm25                                    | 0.2.2           | Apache2.0                                         |       |
| ✅     | Jinja2                                       | 3.1.6           | BSD License                                       |       |
| ✅     | Pygments                                     | 2.19.2          | BSD License                                       |       |
| ✅     | adlfs                                        | 2025.8.0        | BSD License                                       |       |
| ✅     | cobble                                       | 0.1.4           | BSD License                                       |       |
| ✅     | colorama                                     | 0.4.6           | BSD License                                       |       |
| ✅     | contourpy                                    | 1.3.3           | BSD License                                       |       |
| ✅     | cycler                                       | 0.12.1          | BSD License                                       |       |
| ✅     | decorator                                    | 5.2.1           | BSD License                                       |       |
| ✅     | fsspec                                       | 2024.12.0       | BSD License                                       |       |
| ✅     | httpx                                        | 0.28.1          | BSD License                                       |       |
| ✅     | ipython_pygments_lexers                      | 1.1.1           | BSD License                                       |       |
| ✅     | isodate                                      | 0.7.2           | BSD License                                       |       |
| ✅     | joblib                                       | 1.5.2           | BSD License                                       |       |
| ✅     | jsonpatch                                    | 1.33            | BSD License                                       |       |
| ✅     | jsonpointer                                  | 3.0.0           | BSD License                                       |       |
| ✅     | kiwisolver                                   | 1.4.9           | BSD License                                       |       |
| ✅     | lxml                                         | 5.4.0           | BSD License                                       |       |
| ✅     | mammoth                                      | 1.11.0          | BSD License                                       |       |
| ✅     | mpmath                                       | 1.3.0           | BSD License                                       |       |
| ✅     | nest-asyncio                                 | 1.6.0           | BSD License                                       |       |
| ✅     | networkx                                     | 3.5             | BSD License                                       |       |
| ✅     | numpy                                        | 2.3.4           | BSD License                                       |       |
| ✅     | olefile                                      | 0.47            | BSD License                                       |       |
| ✅     | pandas                                       | 2.2.3           | BSD License                                       |       |
| ✅     | prompt_toolkit                               | 3.0.52          | BSD License                                       |       |
| ✅     | pycparser                                    | 2.23            | BSD License                                       |       |
| ✅     | s3fs                                         | 2024.12.0       | BSD License                                       |       |
| ✅     | scipy                                        | 1.16.3          | BSD License                                       |       |
| ✅     | seaborn                                      | 0.13.2          | BSD License                                       |       |
| ✅     | striprtf                                     | 0.0.26          | BSD License                                       |       |
| ✅     | sympy                                        | 1.14.0          | BSD License                                       |       |
| ✅     | traitlets                                    | 5.14.3          | BSD License                                       |       |
| ✅     | uuid_utils                                   | 0.14.0          | BSD License                                       |       |
| ✅     | webencodings                                 | 0.5.1           | BSD License                                       |       |
| ✅     | wrapt                                        | 1.17.3          | BSD License                                       |       |
| ✅     | xlsxwriter                                   | 3.2.9           | BSD License                                       |       |
| ✅     | xxhash                                       | 3.6.0           | BSD License                                       |       |
| ✅     | MarkupSafe                                   | 3.0.3           | BSD-3-Clause                                      |       |
| ✅     | click                                        | 8.3.0           | BSD-3-Clause (override)                           |       |
| ✅     | httpcore                                     | 1.0.9           | BSD-3-Clause                                      |       |
| ✅     | idna                                         | 3.11            | BSD-3-Clause                                      |       |
| ✅     | ipython                                      | 9.7.0           | BSD-3-Clause                                      |       |
| ✅     | portalocker                                  | 3.2.0           | BSD-3-Clause                                      |       |
| ✅     | pypdf                                        | 6.5.0           | BSD-3-Clause (override)                           |       |
| ✅     | python-dotenv                                | 1.2.1           | BSD-3-Clause                                      |       |
| ✅     | starlette                                    | 0.46.2          | BSD-3-Clause                                      |       |
| ✅     | zstandard                                    | 0.25.0          | BSD-3-Clause                                      |       |
| ✅     | dnspython                                    | 2.8.0           | ISC License (ISCL)                                |       |
| ✅     | pexpect                                      | 4.9.0           | ISC License (ISCL)                                |       |
| ✅     | ptyprocess                                   | 0.7.0           | ISC License (ISCL)                                |       |
| ✅     | griffe                                       | 1.14.0          | ISC (override)                                    |       |
| ✅     | greenlet                                     | 3.2.4           | MIT AND Python-2.0                                |       |
| ✅     | Deprecated                                   | 1.3.1           | MIT License                                       |       |
| ✅     | Mako                                         | 1.3.10          | MIT License                                       |       |
| ✅     | PyJWT                                        | 2.10.1          | MIT License                                       |       |
| ✅     | PyYAML                                       | 6.0.3           | MIT License                                       |       |
| ✅     | aiosqlite                                    | 0.21.0          | MIT License                                       |       |
| ✅     | annotated-types                              | 0.7.0           | MIT License                                       |       |
| ✅     | azure-ai-documentintelligence                | 1.0.2           | MIT License                                       |       |
| ✅     | azure-core                                   | 1.36.0          | MIT License                                       |       |
| ✅     | azure-datalake-store                         | 0.0.53          | MIT License                                       |       |
| ✅     | azure-storage-blob                           | 12.27.1         | MIT License                                       |       |
| ✅     | azure-storage-file-datalake                  | 12.22.0         | MIT License                                       |       |
| ✅     | backoff                                      | 2.2.1           | MIT License                                       |       |
| ✅     | beautifulsoup4                               | 4.14.2          | MIT License                                       |       |
| ✅     | cachetools                                   | 5.5.2           | MIT License                                       |       |
| ✅     | cohere                                       | 5.20.0          | MIT License                                       |       |
| ✅     | coloredlogs                                  | 15.0.1          | MIT License                                       |       |
| ✅     | colorlog                                     | 6.10.1          | MIT License                                       |       |
| ✅     | dataclasses-json                             | 0.6.7           | MIT License                                       |       |
| ✅     | et_xmlfile                                   | 2.0.0           | MIT License                                       |       |
| ✅     | executing                                    | 2.2.1           | MIT License                                       |       |
| ✅     | filetype                                     | 1.2.0           | MIT License                                       |       |
| ✅     | h11                                          | 0.16.0          | MIT License                                       |       |
| ✅     | h2                                           | 4.3.0           | MIT License                                       |       |
| ✅     | hpack                                        | 4.1.0           | MIT License                                       |       |
| ✅     | html5lib                                     | 1.1             | MIT License                                       |       |
| ✅     | humanfriendly                                | 10.0            | MIT License                                       |       |
| ✅     | hyperframe                                   | 6.1.0           | MIT License                                       |       |
| ✅     | jedi                                         | 0.19.2          | MIT License                                       |       |
| ✅     | jiter                                        | 0.11.1          | MIT License                                       |       |
| ✅     | jmespath                                     | 1.0.1           | MIT License                                       |       |
| ✅     | json_repair                                  | 0.44.1          | MIT License                                       |       |
| ✅     | langfuse                                     | 3.14.1          | MIT License                                       |       |
| ✅     | markdownify                                  | 1.2.2           | MIT License                                       |       |
| ✅     | marshmallow                                  | 3.26.1          | MIT License                                       |       |
| ✅     | memgraph-toolbox                             | 0.1.9           | MIT License                                       |       |
| ✅     | mongoengine                                  | 0.29.1          | MIT License                                       |       |
| ✅     | msal                                         | 1.34.0          | MIT License                                       |       |
| ✅     | msal-extensions                              | 1.3.1           | MIT License                                       |       |
| ✅     | mypy                                         | 1.18.2          | MIT License                                       |       |
| ✅     | onnxruntime                                  | 1.20.1          | MIT License                                       |       |
| ✅     | openpyxl                                     | 3.1.5           | MIT License                                       |       |
| ✅     | parse                                        | 1.20.2          | MIT License                                       |       |
| ✅     | parso                                        | 0.8.5           | MIT License                                       |       |
| ✅     | pluggy                                       | 1.6.0           | MIT License                                       |       |
| ✅     | posthog                                      | 7.6.0           | MIT License                                       |       |
| ✅     | pure_eval                                    | 0.2.3           | MIT License                                       |       |
| ✅     | pytest                                       | 8.4.2           | MIT License                                       |       |
| ✅     | pytest-bdd                                   | 8.1.0           | MIT License                                       |       |
| ✅     | pytest-mock                                  | 3.15.1          | MIT License                                       |       |
| ✅     | python-i18n                                  | 0.3.9           | MIT License                                       |       |
| ✅     | python-pptx                                  | 1.0.2           | MIT License                                       |       |
| ✅     | pytokens                                     | 0.3.0           | MIT License                                       |       |
| ✅     | pytz                                         | 2025.2          | MIT License                                       |       |
| ✅     | redis                                        | 5.3.1           | MIT License                                       |       |
| ✅     | ruff                                         | 0.8.6           | MIT License                                       |       |
| ✅     | six                                          | 1.17.0          | MIT License                                       |       |
| ✅     | stack-data                                   | 0.6.3           | MIT License                                       |       |
| ✅     | tabulate                                     | 0.9.0           | MIT License                                       |       |
| ✅     | toml-sort                                    | 0.24.3          | MIT License                                       |       |
| ✅     | tomlkit                                      | 0.13.3          | MIT License                                       |       |
| ✅     | types-awscrt                                 | 0.31.1          | MIT License                                       |       |
| ✅     | typing-inspect                               | 0.9.0           | MIT License                                       |       |
| ✅     | tqdm                                         | 4.67.1          | MIT License; Mozilla Public License 2.0 (MPL 2.0) |       |
| ✅     | tiktoken                                     | 0.12.0          | MIT (override)                                    |       |
| ✅     | SQLAlchemy                                   | 2.0.44          | MIT                                               |       |
| ✅     | aioitertools                                 | 0.13.0          | MIT                                               |       |
| ✅     | annotated-doc                                | 0.0.4           | MIT                                               |       |
| ✅     | anyio                                        | 4.11.0          | MIT (override)                                    |       |
| ✅     | attrs                                        | 25.4.0          | MIT (override)                                    |       |
| ✅     | azure-identity                               | 1.25.1          | MIT                                               |       |
| ✅     | banks                                        | 2.2.0           | BSD-3-Clause (override)                           |       |
| ✅     | black                                        | 25.9.0          | MIT                                               |       |
| ✅     | boto3-stubs                                  | 1.42.35         | MIT                                               |       |
| ✅     | botocore-stubs                               | 1.42.35         | MIT                                               |       |
| ✅     | cffi                                         | 2.0.0           | MIT                                               |       |
| ✅     | charset-normalizer                           | 3.4.4           | MIT                                               |       |
| ✅     | fastapi                                      | 0.128.0         | MIT                                               |       |
| ✅     | fastavro                                     | 1.12.1          | MIT                                               |       |
| ✅     | fonttools                                    | 4.60.1          | MIT                                               |       |
| ✅     | gherkin-official                             | 29.0.0          | MIT                                               |       |
| ✅     | httpx-sse                                    | 0.4.0           | MIT                                               |       |
| ✅     | iniconfig                                    | 2.3.0           | MIT                                               |       |
| ✅     | kuzu                                         | 0.11.3          | MIT                                               |       |
| ✅     | langchain                                    | 1.2.7           | MIT                                               |       |
| ✅     | langchain-aws                                | 1.1.0           | MIT                                               |       |
| ✅     | langchain-classic                            | 1.0.1           | MIT                                               |       |
| ✅     | langchain-core                               | 1.2.7           | MIT                                               |       |
| ✅     | langchain-memgraph                           | 0.1.12          | MIT                                               |       |
| ✅     | langchain-neo4j                              | 0.8.0           | MIT                                               |       |
| ✅     | langchain-text-splitters                     | 1.1.0           | MIT                                               |       |
| ✅     | langgraph                                    | 1.0.7           | MIT                                               |       |
| ✅     | langgraph-checkpoint                         | 4.0.0           | MIT                                               |       |
| ✅     | langgraph-prebuilt                           | 1.0.7           | MIT                                               |       |
| ✅     | langgraph-sdk                                | 0.3.3           | MIT                                               |       |
| ✅     | langsmith                                    | 0.6.5           | MIT                                               |       |
| ✅     | llama-index-core                             | 0.14.12         | MIT (override)                                    |       |
| ✅     | llama-index-embeddings-openai                | 0.5.1           | MIT                                               |       |
| ✅     | llama-index-embeddings-openai-like           | 0.2.2           | MIT (override)                                    |       |
| ✅     | llama-index-instrumentation                  | 0.4.2           | MIT (override)                                    |       |
| ✅     | llama-index-llms-azure-openai                | 0.4.2           | MIT                                               |       |
| ✅     | llama-index-llms-openai                      | 0.6.12          | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai-like                 | 0.5.3           | MIT (override)                                    |       |
| ✅     | llama-index-postprocessor-cohere-rerank      | 0.5.1           | MIT                                               |       |
| ✅     | llama-index-readers-file                     | 0.5.6           | MIT (override)                                    |       |
| ✅     | llama-index-storage-docstore-mongodb         | 0.4.1           | MIT                                               |       |
| ✅     | llama-index-storage-kvstore-mongodb          | 0.4.1           | MIT                                               |       |
| ✅     | llama-index-vector-stores-milvus             | 0.9.4           | MIT (override)                                    |       |
| ✅     | llama-index-workflows                        | 2.11.6          | MIT (override)                                    |       |
| ✅     | markitdown                                   | 0.1.4           | MIT                                               |       |
| ✅     | mypy-boto3-s3                                | 1.42.21         | MIT                                               |       |
| ✅     | mypy_extensions                              | 1.1.0           | MIT (override)                                    |       |
| ✅     | parse_type                                   | 0.6.6           | MIT (override)                                    |       |
| ✅     | platformdirs                                 | 4.5.0           | MIT                                               |       |
| ✅     | pydantic                                     | 2.12.4          | MIT                                               |       |
| ✅     | pydantic-settings                            | 2.11.0          | MIT                                               |       |
| ✅     | pydantic_core                                | 2.41.5          | MIT                                               |       |
| ✅     | pyparsing                                    | 3.2.5           | MIT                                               |       |
| ✅     | pytest-cov                                   | 6.3.0           | MIT                                               |       |
| ✅     | soupsieve                                    | 2.8             | MIT                                               |       |
| ✅     | stringcase                                   | 1.2.0           | MIT                                               |       |
| ✅     | tokenize_rt                                  | 6.2.0           | MIT                                               |       |
| ✅     | types-s3transfer                             | 0.16.0          | MIT                                               |       |
| ✅     | typing-inspection                            | 0.4.2           | MIT (override)                                    |       |
| ✅     | urllib3                                      | 2.5.0           | MIT (override)                                    |       |
| ✅     | zipp                                         | 3.23.0          | MIT (override)                                    |       |
| ✅     | pillow                                       | 12.0.0          | MIT-CMU (override)                                |       |
| ✅     | certifi                                      | 2025.10.5       | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | pathspec                                     | 0.12.1          | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | typing_extensions                            | 4.15.0          | PSF-2.0 (override)                                |       |
| ✅     | aiohappyeyeballs                             | 2.6.1           | Python Software Foundation License                |       |
| ✅     | defusedxml                                   | 0.7.1           | Python Software Foundation License                |       |
| ✅     | matplotlib                                   | 3.10.7          | Python Software Foundation License                |       |
| ✅     | matplotlib-inline                            | 0.2.1           | BSD-3-Clause (override)                           |       |
| ✅     | filelock                                     | 3.20.0          | Unlicense                                         |       |

### aihub_process

| Status | Package                                      | Version         | License                                           | Notes |
| ------ | -------------------------------------------- | --------------- | ------------------------------------------------- | ----- |
| ✅     | protobuf                                     | 5.29.5          | 3-Clause BSD License                              |       |
| ✅     | dirtyjson                                    | 1.0.8           | Academic Free License (AFL); MIT License          |       |
| ✅     | asttokens                                    | 3.0.0           | Apache 2.0                                        |       |
| ✅     | multidict                                    | 6.7.0           | Apache License 2.0                                |       |
| ✅     | neo4j-graphrag                               | 1.12.0          | Apache-2.0 (override)                             |       |
| ✅     | aiosignal                                    | 1.4.0           | Apache Software License                           |       |
| ✅     | distro                                       | 1.9.0           | Apache Software License                           |       |
| ✅     | flatbuffers                                  | 25.12.19        | Apache Software License                           |       |
| ✅     | googleapis-common-protos                     | 1.71.0          | Apache Software License                           |       |
| ✅     | grpcio                                       | 1.76.0          | Apache Software License                           |       |
| ✅     | huggingface-hub                              | 0.36.0          | Apache Software License                           |       |
| ✅     | importlib_metadata                           | 8.7.0           | Apache Software License                           |       |
| ✅     | magika                                       | 0.6.3           | Apache Software License                           |       |
| ✅     | motor                                        | 3.7.1           | Apache Software License                           |       |
| ✅     | nats-py                                      | 2.12.0          | Apache Software License                           |       |
| ✅     | nltk                                         | 3.9.2           | Apache Software License                           |       |
| ✅     | openai                                       | 1.109.1         | Apache Software License                           |       |
| ✅     | opentelemetry-instrumentation-milvus         | 0.47.5          | Apache Software License                           |       |
| ✅     | opentelemetry-semantic-conventions-ai        | 0.4.13          | Apache Software License                           |       |
| ✅     | propcache                                    | 0.4.1           | Apache Software License                           |       |
| ✅     | pymilvus                                     | 2.6.3           | Apache Software License                           |       |
| ✅     | pymongo                                      | 4.15.3          | Apache Software License                           |       |
| ✅     | pytest-asyncio                               | 0.24.0          | Apache Software License                           |       |
| ✅     | qdrant-client                                | 1.16.2          | Apache Software License                           |       |
| ✅     | requests                                     | 2.32.5          | Apache Software License                           |       |
| ✅     | requests-toolbelt                            | 1.0.0           | Apache Software License                           |       |
| ✅     | s3transfer                                   | 0.15.0          | Apache Software License                           |       |
| ✅     | safetensors                                  | 0.6.2           | Apache Software License                           |       |
| ✅     | tenacity                                     | 9.1.2           | Apache Software License                           |       |
| ✅     | tokenizers                                   | 0.22.1          | Apache Software License                           |       |
| ✅     | transformers                                 | 4.57.3          | Apache Software License                           |       |
| ✅     | tzdata                                       | 2025.2          | Apache Software License                           |       |
| ✅     | yarl                                         | 1.22.0          | Apache Software License                           |       |
| ✅     | packaging                                    | 25.0            | Apache Software License; BSD License              |       |
| ✅     | python-dateutil                              | 2.9.0.post0     | Apache Software License; BSD License              |       |
| ✅     | sniffio                                      | 1.3.1           | Apache Software License; MIT License              |       |
| ✅     | uvloop                                       | 0.22.1          | Apache Software License; MIT License              |       |
| ✅     | regex                                        | 2025.11.3       | Apache-2.0 (override)                             |       |
| ✅     | aiohttp                                      | 3.13.2          | Apache-2.0 AND MIT                                |       |
| ✅     | neo4j                                        | 6.1.0           | Apache-2.0 AND Python-2.0                         |       |
| ✅     | cryptography                                 | 46.0.3          | Apache-2.0 OR BSD-3-Clause                        |       |
| ✅     | orjson                                       | 3.11.4          | Apache-2.0 OR MIT                                 |       |
| ✅     | ormsgpack                                    | 1.12.2          | Apache-2.0 OR MIT                                 |       |
| ✅     | aiobotocore                                  | 2.26.0          | Apache-2.0                                        |       |
| ✅     | boto3                                        | 1.41.5          | Apache-2.0                                        |       |
| ✅     | botocore                                     | 1.41.5          | Apache-2.0                                        |       |
| ✅     | coverage                                     | 7.11.0          | Apache-2.0                                        |       |
| ✅     | frozenlist                                   | 1.8.0           | Apache-2.0                                        |       |
| ✅     | hf-xet                                       | 1.2.0           | Apache-2.0 (override)                             |       |
| ✅     | mem0ai                                       | 1.0.2           | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation                | 0.1.42          | Apache-2.0                                        |       |
| ✅     | openinference-instrumentation-llama-index    | 4.3.8           | Apache-2.0                                        |       |
| ✅     | openinference-semantic-conventions           | 0.1.25          | Apache-2.0                                        |       |
| ✅     | opentelemetry-api                            | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp                  | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-common     | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc       | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-exporter-otlp-proto-http       | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-instrumentation                | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-asyncio        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-botocore       | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-httpx          | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-jinja2         | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-logging        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-pymongo        | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-redis          | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-instrumentation-requests       | 0.60b1          | Apache-2.0                                        |       |
| ✅     | opentelemetry-propagator-aws-xray            | 1.0.2           | Apache-2.0                                        |       |
| ✅     | opentelemetry-proto                          | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-sdk                            | 1.39.1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-semantic-conventions           | 0.60b1          | Apache-2.0 (override)                             |       |
| ✅     | opentelemetry-util-http                      | 0.60b1          | Apache-2.0                                        |       |
| ✅     | types-PyYAML                                 | 6.0.12.20250915 | Apache-2.0 (override)                             |       |
| ✅     | types-requests                               | 2.32.4.20250913 | Apache-2.0 (override)                             |       |
| ✅     | rank-bm25                                    | 0.2.2           | Apache2.0                                         |       |
| ✅     | Jinja2                                       | 3.1.6           | BSD License                                       |       |
| ✅     | Pygments                                     | 2.19.2          | BSD License                                       |       |
| ✅     | adlfs                                        | 2025.8.0        | BSD License                                       |       |
| ✅     | cobble                                       | 0.1.4           | BSD License                                       |       |
| ✅     | colorama                                     | 0.4.6           | BSD License                                       |       |
| ✅     | decorator                                    | 5.2.1           | BSD License                                       |       |
| ✅     | fsspec                                       | 2024.12.0       | BSD License                                       |       |
| ✅     | httpx                                        | 0.28.1          | BSD License                                       |       |
| ✅     | ipython_pygments_lexers                      | 1.1.1           | BSD License                                       |       |
| ✅     | isodate                                      | 0.7.2           | BSD License                                       |       |
| ✅     | joblib                                       | 1.5.2           | BSD License                                       |       |
| ✅     | jsonpatch                                    | 1.33            | BSD License                                       |       |
| ✅     | jsonpointer                                  | 3.0.0           | BSD License                                       |       |
| ✅     | lxml                                         | 5.4.0           | BSD License                                       |       |
| ✅     | mammoth                                      | 1.11.0          | BSD License                                       |       |
| ✅     | mpmath                                       | 1.3.0           | BSD License                                       |       |
| ✅     | nest-asyncio                                 | 1.6.0           | BSD License                                       |       |
| ✅     | networkx                                     | 3.5             | BSD License                                       |       |
| ✅     | numpy                                        | 2.3.4           | BSD License                                       |       |
| ✅     | olefile                                      | 0.47            | BSD License                                       |       |
| ✅     | pandas                                       | 2.2.3           | BSD License                                       |       |
| ✅     | prompt_toolkit                               | 3.0.52          | BSD License                                       |       |
| ✅     | pycparser                                    | 2.23            | BSD License                                       |       |
| ✅     | s3fs                                         | 2024.12.0       | BSD License                                       |       |
| ✅     | scipy                                        | 1.16.3          | BSD License                                       |       |
| ✅     | striprtf                                     | 0.0.26          | BSD License                                       |       |
| ✅     | sympy                                        | 1.14.0          | BSD License                                       |       |
| ✅     | traitlets                                    | 5.14.3          | BSD License                                       |       |
| ✅     | uuid_utils                                   | 0.14.0          | BSD License                                       |       |
| ✅     | webencodings                                 | 0.5.1           | BSD License                                       |       |
| ✅     | websockets                                   | 15.0.1          | BSD License                                       |       |
| ✅     | wrapt                                        | 1.17.3          | BSD License                                       |       |
| ✅     | xlsxwriter                                   | 3.2.9           | BSD License                                       |       |
| ✅     | xxhash                                       | 3.6.0           | BSD License                                       |       |
| ✅     | MarkupSafe                                   | 3.0.3           | BSD-3-Clause                                      |       |
| ✅     | click                                        | 8.3.0           | BSD-3-Clause (override)                           |       |
| ✅     | httpcore                                     | 1.0.9           | BSD-3-Clause                                      |       |
| ✅     | idna                                         | 3.11            | BSD-3-Clause                                      |       |
| ✅     | ipython                                      | 9.7.0           | BSD-3-Clause                                      |       |
| ✅     | portalocker                                  | 3.2.0           | BSD-3-Clause                                      |       |
| ✅     | pypdf                                        | 6.5.0           | BSD-3-Clause (override)                           |       |
| ✅     | python-dotenv                                | 1.2.1           | BSD-3-Clause                                      |       |
| ✅     | starlette                                    | 0.46.2          | BSD-3-Clause                                      |       |
| ✅     | uvicorn                                      | 0.34.3          | BSD-3-Clause                                      |       |
| ✅     | zstandard                                    | 0.25.0          | BSD-3-Clause                                      |       |
| ✅     | dnspython                                    | 2.8.0           | ISC License (ISCL)                                |       |
| ✅     | pexpect                                      | 4.9.0           | ISC License (ISCL)                                |       |
| ✅     | ptyprocess                                   | 0.7.0           | ISC License (ISCL)                                |       |
| ✅     | griffe                                       | 1.14.0          | ISC (override)                                    |       |
| ✅     | greenlet                                     | 3.2.4           | MIT AND Python-2.0                                |       |
| ✅     | Deprecated                                   | 1.3.1           | MIT License                                       |       |
| ✅     | Mako                                         | 1.3.10          | MIT License                                       |       |
| ✅     | PyJWT                                        | 2.10.1          | MIT License                                       |       |
| ✅     | PyYAML                                       | 6.0.3           | MIT License                                       |       |
| ✅     | aiosqlite                                    | 0.21.0          | MIT License                                       |       |
| ✅     | annotated-types                              | 0.7.0           | MIT License                                       |       |
| ✅     | azure-ai-documentintelligence                | 1.0.2           | MIT License                                       |       |
| ✅     | azure-core                                   | 1.36.0          | MIT License                                       |       |
| ✅     | azure-datalake-store                         | 0.0.53          | MIT License                                       |       |
| ✅     | azure-storage-blob                           | 12.27.1         | MIT License                                       |       |
| ✅     | azure-storage-file-datalake                  | 12.22.0         | MIT License                                       |       |
| ✅     | backoff                                      | 2.2.1           | MIT License                                       |       |
| ✅     | beautifulsoup4                               | 4.14.2          | MIT License                                       |       |
| ✅     | cachetools                                   | 5.5.2           | MIT License                                       |       |
| ✅     | cohere                                       | 5.20.0          | MIT License                                       |       |
| ✅     | coloredlogs                                  | 15.0.1          | MIT License                                       |       |
| ✅     | colorlog                                     | 6.10.1          | MIT License                                       |       |
| ✅     | dataclasses-json                             | 0.6.7           | MIT License                                       |       |
| ✅     | et_xmlfile                                   | 2.0.0           | MIT License                                       |       |
| ✅     | executing                                    | 2.2.1           | MIT License                                       |       |
| ✅     | filetype                                     | 1.2.0           | MIT License                                       |       |
| ✅     | h11                                          | 0.16.0          | MIT License                                       |       |
| ✅     | h2                                           | 4.3.0           | MIT License                                       |       |
| ✅     | hpack                                        | 4.1.0           | MIT License                                       |       |
| ✅     | html5lib                                     | 1.1             | MIT License                                       |       |
| ✅     | humanfriendly                                | 10.0            | MIT License                                       |       |
| ✅     | hyperframe                                   | 6.1.0           | MIT License                                       |       |
| ✅     | jedi                                         | 0.19.2          | MIT License                                       |       |
| ✅     | jiter                                        | 0.11.1          | MIT License                                       |       |
| ✅     | jmespath                                     | 1.0.1           | MIT License                                       |       |
| ✅     | json_repair                                  | 0.44.1          | MIT License                                       |       |
| ✅     | langfuse                                     | 3.14.1          | MIT License                                       |       |
| ✅     | markdownify                                  | 1.2.2           | MIT License                                       |       |
| ✅     | marshmallow                                  | 3.26.1          | MIT License                                       |       |
| ✅     | memgraph-toolbox                             | 0.1.9           | MIT License                                       |       |
| ✅     | mongoengine                                  | 0.29.1          | MIT License                                       |       |
| ✅     | msal                                         | 1.34.0          | MIT License                                       |       |
| ✅     | msal-extensions                              | 1.3.1           | MIT License                                       |       |
| ✅     | mypy                                         | 1.18.2          | MIT License                                       |       |
| ✅     | onnxruntime                                  | 1.20.1          | MIT License                                       |       |
| ✅     | openpyxl                                     | 3.1.5           | MIT License                                       |       |
| ✅     | parse                                        | 1.20.2          | MIT License                                       |       |
| ✅     | parso                                        | 0.8.5           | MIT License                                       |       |
| ✅     | pluggy                                       | 1.6.0           | MIT License                                       |       |
| ✅     | posthog                                      | 7.6.0           | MIT License                                       |       |
| ✅     | pure_eval                                    | 0.2.3           | MIT License                                       |       |
| ✅     | pytest                                       | 8.4.2           | MIT License                                       |       |
| ✅     | pytest-bdd                                   | 8.1.0           | MIT License                                       |       |
| ✅     | pytest-mock                                  | 3.15.1          | MIT License                                       |       |
| ✅     | python-i18n                                  | 0.3.9           | MIT License                                       |       |
| ✅     | python-pptx                                  | 1.0.2           | MIT License                                       |       |
| ✅     | pytokens                                     | 0.3.0           | MIT License                                       |       |
| ✅     | pytz                                         | 2025.2          | MIT License                                       |       |
| ✅     | redis                                        | 5.3.1           | MIT License                                       |       |
| ✅     | ruff                                         | 0.8.6           | MIT License                                       |       |
| ✅     | six                                          | 1.17.0          | MIT License                                       |       |
| ✅     | stack-data                                   | 0.6.3           | MIT License                                       |       |
| ✅     | tabulate                                     | 0.9.0           | MIT License                                       |       |
| ✅     | toml-sort                                    | 0.24.3          | MIT License                                       |       |
| ✅     | tomlkit                                      | 0.13.3          | MIT License                                       |       |
| ✅     | types-awscrt                                 | 0.31.1          | MIT License                                       |       |
| ✅     | typing-inspect                               | 0.9.0           | MIT License                                       |       |
| ✅     | watchfiles                                   | 1.1.1           | MIT License                                       |       |
| ✅     | tqdm                                         | 4.67.1          | MIT License; Mozilla Public License 2.0 (MPL 2.0) |       |
| ✅     | tiktoken                                     | 0.12.0          | MIT (override)                                    |       |
| ✅     | SQLAlchemy                                   | 2.0.44          | MIT                                               |       |
| ✅     | aioitertools                                 | 0.13.0          | MIT                                               |       |
| ✅     | annotated-doc                                | 0.0.4           | MIT                                               |       |
| ✅     | anyio                                        | 4.11.0          | MIT (override)                                    |       |
| ✅     | asgi-lifespan                                | 2.1.0           | MIT                                               |       |
| ✅     | attrs                                        | 25.4.0          | MIT (override)                                    |       |
| ✅     | azure-identity                               | 1.25.1          | MIT                                               |       |
| ✅     | banks                                        | 2.2.0           | BSD-3-Clause (override)                           |       |
| ✅     | black                                        | 25.9.0          | MIT                                               |       |
| ✅     | boto3-stubs                                  | 1.42.35         | MIT                                               |       |
| ✅     | botocore-stubs                               | 1.42.35         | MIT                                               |       |
| ✅     | cffi                                         | 2.0.0           | MIT                                               |       |
| ✅     | charset-normalizer                           | 3.4.4           | MIT                                               |       |
| ✅     | fastapi                                      | 0.128.0         | MIT                                               |       |
| ✅     | fastavro                                     | 1.12.1          | MIT                                               |       |
| ✅     | gherkin-official                             | 29.0.0          | MIT                                               |       |
| ✅     | httptools                                    | 0.7.1           | MIT                                               |       |
| ✅     | httpx-sse                                    | 0.4.0           | MIT                                               |       |
| ✅     | iniconfig                                    | 2.3.0           | MIT                                               |       |
| ✅     | kuzu                                         | 0.11.3          | MIT                                               |       |
| ✅     | langchain                                    | 1.2.7           | MIT                                               |       |
| ✅     | langchain-aws                                | 1.1.0           | MIT                                               |       |
| ✅     | langchain-classic                            | 1.0.1           | MIT                                               |       |
| ✅     | langchain-core                               | 1.2.7           | MIT                                               |       |
| ✅     | langchain-memgraph                           | 0.1.12          | MIT                                               |       |
| ✅     | langchain-neo4j                              | 0.8.0           | MIT                                               |       |
| ✅     | langchain-text-splitters                     | 1.1.0           | MIT                                               |       |
| ✅     | langgraph                                    | 1.0.7           | MIT                                               |       |
| ✅     | langgraph-checkpoint                         | 4.0.0           | MIT                                               |       |
| ✅     | langgraph-prebuilt                           | 1.0.7           | MIT                                               |       |
| ✅     | langgraph-sdk                                | 0.3.3           | MIT                                               |       |
| ✅     | langsmith                                    | 0.6.5           | MIT                                               |       |
| ✅     | llama-index-core                             | 0.14.12         | MIT (override)                                    |       |
| ✅     | llama-index-embeddings-openai                | 0.5.1           | MIT                                               |       |
| ✅     | llama-index-embeddings-openai-like           | 0.2.2           | MIT (override)                                    |       |
| ✅     | llama-index-instrumentation                  | 0.4.2           | MIT (override)                                    |       |
| ✅     | llama-index-llms-azure-openai                | 0.4.2           | MIT                                               |       |
| ✅     | llama-index-llms-openai                      | 0.6.12          | MIT (override)                                    |       |
| ✅     | llama-index-llms-openai-like                 | 0.5.3           | MIT (override)                                    |       |
| ✅     | llama-index-postprocessor-cohere-rerank      | 0.5.1           | MIT                                               |       |
| ✅     | llama-index-readers-file                     | 0.5.6           | MIT (override)                                    |       |
| ✅     | llama-index-storage-docstore-mongodb         | 0.4.1           | MIT                                               |       |
| ✅     | llama-index-storage-kvstore-mongodb          | 0.4.1           | MIT                                               |       |
| ✅     | llama-index-vector-stores-milvus             | 0.9.4           | MIT (override)                                    |       |
| ✅     | llama-index-workflows                        | 2.11.6          | MIT (override)                                    |       |
| ✅     | markitdown                                   | 0.1.4           | MIT                                               |       |
| ✅     | mypy-boto3-s3                                | 1.42.21         | MIT                                               |       |
| ✅     | mypy_extensions                              | 1.1.0           | MIT (override)                                    |       |
| ✅     | parse_type                                   | 0.6.6           | MIT (override)                                    |       |
| ✅     | platformdirs                                 | 4.5.0           | MIT                                               |       |
| ✅     | pydantic                                     | 2.12.4          | MIT                                               |       |
| ✅     | pydantic-settings                            | 2.11.0          | MIT                                               |       |
| ✅     | pydantic_core                                | 2.41.5          | MIT                                               |       |
| ✅     | pytest-cov                                   | 6.3.0           | MIT                                               |       |
| ✅     | soupsieve                                    | 2.8             | MIT                                               |       |
| ✅     | stringcase                                   | 1.2.0           | MIT                                               |       |
| ✅     | tokenize_rt                                  | 6.2.0           | MIT                                               |       |
| ✅     | types-s3transfer                             | 0.16.0          | MIT                                               |       |
| ✅     | typing-inspection                            | 0.4.2           | MIT (override)                                    |       |
| ✅     | urllib3                                      | 2.5.0           | MIT (override)                                    |       |
| ✅     | zipp                                         | 3.23.0          | MIT (override)                                    |       |
| ✅     | pillow                                       | 12.0.0          | MIT-CMU (override)                                |       |
| ✅     | certifi                                      | 2025.10.5       | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | pathspec                                     | 0.12.1          | Mozilla Public License 2.0 (MPL 2.0)              |       |
| ✅     | typing_extensions                            | 4.15.0          | PSF-2.0 (override)                                |       |
| ✅     | aiohappyeyeballs                             | 2.6.1           | Python Software Foundation License                |       |
| ✅     | defusedxml                                   | 0.7.1           | Python Software Foundation License                |       |
| ✅     | matplotlib-inline                            | 0.2.1           | BSD-3-Clause (override)                           |       |
| ✅     | filelock                                     | 3.20.0          | Unlicense                                         |       |

### aihub_pipeline

| Status | Package                                      | Version         | License                                             | Notes |
| ------ | -------------------------------------------- | --------------- | --------------------------------------------------- | ----- |
| ✅     | protobuf                                     | 5.29.5          | 3-Clause BSD License                                |       |
| ✅     | dirtyjson                                    | 1.0.8           | Academic Free License (AFL); MIT License            |       |
| ✅     | multidict                                    | 6.7.0           | Apache License 2.0                                  |       |
| ✅     | neo4j-graphrag                               | 1.12.0          | Apache-2.0 (override)                               |       |
| ✅     | aiosignal                                    | 1.4.0           | Apache Software License                             |       |
| ✅     | dagster                                      | 1.11.16         | Apache Software License                             |       |
| ✅     | dagster-aws                                  | 0.27.16         | Apache Software License                             |       |
| ✅     | dagster-azure                                | 0.27.16         | Apache Software License                             |       |
| ✅     | dagster-graphql                              | 1.11.16         | Apache Software License                             |       |
| ✅     | dagster-pipes                                | 1.11.16         | Apache Software License                             |       |
| ✅     | dagster-postgres                             | 0.27.16         | Apache Software License                             |       |
| ✅     | dagster-webserver                            | 1.11.16         | Apache Software License                             |       |
| ✅     | dagster_shared                               | 1.11.16         | Apache Software License                             |       |
| ✅     | distro                                       | 1.9.0           | Apache Software License                             |       |
| ✅     | flatbuffers                                  | 25.12.19        | Apache Software License                             |       |
| ✅     | googleapis-common-protos                     | 1.71.0          | Apache Software License                             |       |
| ✅     | grpcio                                       | 1.76.0          | Apache Software License                             |       |
| ✅     | grpcio-health-checking                       | 1.71.2          | Apache Software License                             |       |
| ✅     | huggingface-hub                              | 0.36.0          | Apache Software License                             |       |
| ✅     | importlib_metadata                           | 8.7.0           | Apache Software License                             |       |
| ✅     | magika                                       | 0.6.3           | Apache Software License                             |       |
| ✅     | motor                                        | 3.7.1           | Apache Software License                             |       |
| ✅     | nats-py                                      | 2.12.0          | Apache Software License                             |       |
| ✅     | nltk                                         | 3.9.2           | Apache Software License                             |       |
| ✅     | openai                                       | 1.109.1         | Apache Software License                             |       |
| ✅     | opentelemetry-instrumentation-milvus         | 0.47.5          | Apache Software License                             |       |
| ✅     | opentelemetry-semantic-conventions-ai        | 0.4.13          | Apache Software License                             |       |
| ✅     | propcache                                    | 0.4.1           | Apache Software License                             |       |
| ✅     | pymilvus                                     | 2.6.3           | Apache Software License                             |       |
| ✅     | pymongo                                      | 4.15.3          | Apache Software License                             |       |
| ✅     | pytest-asyncio                               | 0.24.0          | Apache Software License                             |       |
| ✅     | qdrant-client                                | 1.16.2          | Apache Software License                             |       |
| ✅     | requests                                     | 2.32.5          | Apache Software License                             |       |
| ✅     | requests-toolbelt                            | 1.0.0           | Apache Software License                             |       |
| ✅     | s3transfer                                   | 0.15.0          | Apache Software License                             |       |
| ✅     | safetensors                                  | 0.6.2           | Apache Software License                             |       |
| ✅     | tenacity                                     | 9.1.2           | Apache Software License                             |       |
| ✅     | tokenizers                                   | 0.22.1          | Apache Software License                             |       |
| ✅     | toposort                                     | 1.10            | Apache Software License                             |       |
| ✅     | transformers                                 | 4.57.3          | Apache Software License                             |       |
| ✅     | tzdata                                       | 2025.2          | Apache Software License                             |       |
| ✅     | watchdog                                     | 6.0.0           | Apache Software License                             |       |
| ✅     | yarl                                         | 1.22.0          | Apache Software License                             |       |
| ✅     | packaging                                    | 25.0            | Apache Software License; BSD License                |       |
| ✅     | python-dateutil                              | 2.9.0.post0     | Apache Software License; BSD License                |       |
| ✅     | sniffio                                      | 1.3.1           | Apache Software License; MIT License                |       |
| ✅     | uvloop                                       | 0.22.1          | Apache Software License; MIT License                |       |
| ✅     | regex                                        | 2025.11.3       | Apache-2.0 (override)                               |       |
| ✅     | aiohttp                                      | 3.13.2          | Apache-2.0 AND MIT                                  |       |
| ✅     | neo4j                                        | 6.1.0           | Apache-2.0 AND Python-2.0                           |       |
| ✅     | cryptography                                 | 46.0.3          | Apache-2.0 OR BSD-3-Clause                          |       |
| ✅     | orjson                                       | 3.11.4          | Apache-2.0 OR MIT                                   |       |
| ✅     | ormsgpack                                    | 1.12.2          | Apache-2.0 OR MIT                                   |       |
| ✅     | aiobotocore                                  | 2.26.0          | Apache-2.0                                          |       |
| ✅     | boto3                                        | 1.41.5          | Apache-2.0                                          |       |
| ✅     | botocore                                     | 1.41.5          | Apache-2.0                                          |       |
| ✅     | coverage                                     | 7.11.0          | Apache-2.0                                          |       |
| ✅     | frozenlist                                   | 1.8.0           | Apache-2.0                                          |       |
| ✅     | hf-xet                                       | 1.2.0           | Apache-2.0 (override)                               |       |
| ✅     | mem0ai                                       | 1.0.2           | Apache-2.0                                          |       |
| ✅     | openinference-instrumentation                | 0.1.42          | Apache-2.0                                          |       |
| ✅     | openinference-instrumentation-llama-index    | 4.3.8           | Apache-2.0                                          |       |
| ✅     | openinference-semantic-conventions           | 0.1.25          | Apache-2.0                                          |       |
| ✅     | opentelemetry-api                            | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-exporter-otlp                  | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-exporter-otlp-proto-common     | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-exporter-otlp-proto-grpc       | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-exporter-otlp-proto-http       | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-instrumentation                | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-aiohttp-client | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-asyncio        | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-botocore       | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-httpx          | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-jinja2         | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-logging        | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-pymongo        | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-redis          | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-instrumentation-requests       | 0.60b1          | Apache-2.0                                          |       |
| ✅     | opentelemetry-propagator-aws-xray            | 1.0.2           | Apache-2.0                                          |       |
| ✅     | opentelemetry-proto                          | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-sdk                            | 1.39.1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-semantic-conventions           | 0.60b1          | Apache-2.0 (override)                               |       |
| ✅     | opentelemetry-util-http                      | 0.60b1          | Apache-2.0                                          |       |
| ✅     | types-PyYAML                                 | 6.0.12.20250915 | Apache-2.0 (override)                               |       |
| ✅     | types-requests                               | 2.32.4.20250913 | Apache-2.0 (override)                               |       |
| ✅     | rank-bm25                                    | 0.2.2           | Apache2.0                                           |       |
| ✅     | Jinja2                                       | 3.1.6           | BSD License                                         |       |
| ✅     | Pygments                                     | 2.19.2          | BSD License                                         |       |
| ✅     | adlfs                                        | 2025.8.0        | BSD License                                         |       |
| ✅     | cobble                                       | 0.1.4           | BSD License                                         |       |
| ✅     | colorama                                     | 0.4.6           | BSD License                                         |       |
| ✅     | contourpy                                    | 1.3.3           | BSD License                                         |       |
| ✅     | cycler                                       | 0.12.1          | BSD License                                         |       |
| ✅     | fsspec                                       | 2024.12.0       | BSD License                                         |       |
| ✅     | httpx                                        | 0.28.1          | BSD License                                         |       |
| ✅     | isodate                                      | 0.7.2           | BSD License                                         |       |
| ✅     | joblib                                       | 1.5.2           | BSD License                                         |       |
| ✅     | jsonpatch                                    | 1.33            | BSD License                                         |       |
| ✅     | jsonpointer                                  | 3.0.0           | BSD License                                         |       |
| ✅     | kiwisolver                                   | 1.4.9           | BSD License                                         |       |
| ✅     | lxml                                         | 5.4.0           | BSD License                                         |       |
| ✅     | mammoth                                      | 1.11.0          | BSD License                                         |       |
| ✅     | mpmath                                       | 1.3.0           | BSD License                                         |       |
| ✅     | nest-asyncio                                 | 1.6.0           | BSD License                                         |       |
| ✅     | networkx                                     | 3.5             | BSD License                                         |       |
| ✅     | numpy                                        | 2.3.4           | BSD License                                         |       |
| ✅     | olefile                                      | 0.47            | BSD License                                         |       |
| ✅     | pandas                                       | 2.2.3           | BSD License                                         |       |
| ✅     | pycparser                                    | 2.23            | BSD License                                         |       |
| ✅     | s3fs                                         | 2024.12.0       | BSD License                                         |       |
| ✅     | scipy                                        | 1.16.3          | BSD License                                         |       |
| ✅     | striprtf                                     | 0.0.26          | BSD License                                         |       |
| ✅     | sympy                                        | 1.14.0          | BSD License                                         |       |
| ✅     | uuid_utils                                   | 0.14.0          | BSD License                                         |       |
| ✅     | webencodings                                 | 0.5.1           | BSD License                                         |       |
| ✅     | websockets                                   | 15.0.1          | BSD License                                         |       |
| ✅     | wrapt                                        | 1.17.3          | BSD License                                         |       |
| ✅     | xlsxwriter                                   | 3.2.9           | BSD License                                         |       |
| ✅     | xxhash                                       | 3.6.0           | BSD License                                         |       |
| ✅     | antlr4-python3-runtime                       | 4.13.2          | BSD                                                 |       |
| ✅     | MarkupSafe                                   | 3.0.3           | BSD-3-Clause                                        |       |
| ✅     | click                                        | 8.3.0           | BSD-3-Clause (override)                             |       |
| ✅     | httpcore                                     | 1.0.9           | BSD-3-Clause                                        |       |
| ✅     | idna                                         | 3.11            | BSD-3-Clause                                        |       |
| ✅     | portalocker                                  | 3.2.0           | BSD-3-Clause                                        |       |
| ✅     | pypdf                                        | 6.5.0           | BSD-3-Clause (override)                             |       |
| ✅     | python-dotenv                                | 1.2.1           | BSD-3-Clause                                        |       |
| ✅     | starlette                                    | 0.46.2          | BSD-3-Clause                                        |       |
| ✅     | uvicorn                                      | 0.38.0          | BSD-3-Clause                                        |       |
| ✅     | zstandard                                    | 0.25.0          | BSD-3-Clause                                        |       |
| ✅     | psycopg2-binary                              | 2.9.11          | GNU Library or Lesser General Public License (LGPL) |       |
| ✅     | dnspython                                    | 2.8.0           | ISC License (ISCL)                                  |       |
| ✅     | griffe                                       | 1.14.0          | ISC (override)                                      |       |
| ✅     | greenlet                                     | 3.2.4           | MIT AND Python-2.0                                  |       |
| ✅     | Deprecated                                   | 1.3.1           | MIT License                                         |       |
| ✅     | Mako                                         | 1.3.10          | MIT License                                         |       |
| ✅     | PyJWT                                        | 2.10.1          | MIT License                                         |       |
| ✅     | PyYAML                                       | 6.0.3           | MIT License                                         |       |
| ✅     | aioitertools                                 | 0.12.0          | MIT License                                         |       |
| ✅     | aiosqlite                                    | 0.21.0          | MIT License                                         |       |
| ✅     | annotated-types                              | 0.7.0           | MIT License                                         |       |
| ✅     | azure-ai-documentintelligence                | 1.0.2           | MIT License                                         |       |
| ✅     | azure-core                                   | 1.36.0          | MIT License                                         |       |
| ✅     | azure-datalake-store                         | 0.0.53          | MIT License                                         |       |
| ✅     | azure-storage-blob                           | 12.27.1         | MIT License                                         |       |
| ✅     | azure-storage-file-datalake                  | 12.22.0         | MIT License                                         |       |
| ✅     | backoff                                      | 2.2.1           | MIT License                                         |       |
| ✅     | beautifulsoup4                               | 4.14.2          | MIT License                                         |       |
| ✅     | cachetools                                   | 5.5.2           | MIT License                                         |       |
| ✅     | cohere                                       | 5.20.0          | MIT License                                         |       |
| ✅     | coloredlogs                                  | 14.0            | MIT License                                         |       |
| ✅     | colorlog                                     | 6.10.1          | MIT License                                         |       |
| ✅     | dataclasses-json                             | 0.6.7           | MIT License                                         |       |
| ✅     | docstring_parser                             | 0.17.0          | MIT License                                         |       |
| ✅     | et_xmlfile                                   | 2.0.0           | MIT License                                         |       |
| ✅     | filetype                                     | 1.2.0           | MIT License                                         |       |
| ✅     | graphql-core                                 | 3.2.6           | MIT License                                         |       |
| ✅     | graphql-relay                                | 3.2.0           | MIT License                                         |       |
| ✅     | h11                                          | 0.16.0          | MIT License                                         |       |
| ✅     | h2                                           | 4.3.0           | MIT License                                         |       |
| ✅     | hpack                                        | 4.1.0           | MIT License                                         |       |
| ✅     | html5lib                                     | 1.1             | MIT License                                         |       |
| ✅     | humanfriendly                                | 10.0            | MIT License                                         |       |
| ✅     | hyperframe                                   | 6.1.0           | MIT License                                         |       |
| ✅     | jiter                                        | 0.11.1          | MIT License                                         |       |
| ✅     | jmespath                                     | 1.0.1           | MIT License                                         |       |
| ✅     | json_repair                                  | 0.44.1          | MIT License                                         |       |
| ✅     | langfuse                                     | 3.14.1          | MIT License                                         |       |
| ✅     | markdown-it-py                               | 4.0.0           | MIT License                                         |       |
| ✅     | markdownify                                  | 1.2.2           | MIT License                                         |       |
| ✅     | marshmallow                                  | 3.26.1          | MIT License                                         |       |
| ✅     | mdurl                                        | 0.1.2           | MIT License                                         |       |
| ✅     | memgraph-toolbox                             | 0.1.9           | MIT License                                         |       |
| ✅     | mongoengine                                  | 0.29.1          | MIT License                                         |       |
| ✅     | msal                                         | 1.34.0          | MIT License                                         |       |
| ✅     | msal-extensions                              | 1.3.1           | MIT License                                         |       |
| ✅     | mypy                                         | 1.18.2          | MIT License                                         |       |
| ✅     | onnxruntime                                  | 1.20.1          | MIT License                                         |       |
| ✅     | openpyxl                                     | 3.1.5           | MIT License                                         |       |
| ✅     | pluggy                                       | 1.6.0           | MIT License                                         |       |
| ✅     | posthog                                      | 7.6.0           | MIT License                                         |       |
| ✅     | pytest                                       | 8.4.2           | MIT License                                         |       |
| ✅     | pytest-mock                                  | 3.15.1          | MIT License                                         |       |
| ✅     | python-i18n                                  | 0.3.9           | MIT License                                         |       |
| ✅     | python-pptx                                  | 1.0.2           | MIT License                                         |       |
| ✅     | pytz                                         | 2025.2          | MIT License                                         |       |
| ✅     | redis                                        | 5.3.1           | MIT License                                         |       |
| ✅     | rich                                         | 14.2.0          | MIT License                                         |       |
| ✅     | ruff                                         | 0.8.6           | MIT License                                         |       |
| ✅     | six                                          | 1.17.0          | MIT License                                         |       |
| ✅     | tabulate                                     | 0.9.0           | MIT License                                         |       |
| ✅     | tomlkit                                      | 0.13.3          | MIT License                                         |       |
| ✅     | types-awscrt                                 | 0.31.1          | MIT License                                         |       |
| ✅     | typing-inspect                               | 0.9.0           | MIT License                                         |       |
| ✅     | watchfiles                                   | 1.1.1           | MIT License                                         |       |
| ✅     | tqdm                                         | 4.67.1          | MIT License; Mozilla Public License 2.0 (MPL 2.0)   |       |
| ✅     | tiktoken                                     | 0.12.0          | MIT (override)                                      |       |
| ✅     | structlog                                    | 25.5.0          | MIT OR Apache-2.0                                   |       |
| ✅     | SQLAlchemy                                   | 2.0.44          | MIT                                                 |       |
| ✅     | alembic                                      | 1.17.1          | MIT (override)                                      |       |
| ✅     | annotated-doc                                | 0.0.4           | MIT                                                 |       |
| ✅     | anyio                                        | 4.11.0          | MIT (override)                                      |       |
| ✅     | attrs                                        | 25.4.0          | MIT (override)                                      |       |
| ✅     | azure-identity                               | 1.25.1          | MIT                                                 |       |
| ✅     | banks                                        | 2.2.0           | BSD-3-Clause (override)                             |       |
| ✅     | boto3-stubs                                  | 1.42.35         | MIT                                                 |       |
| ✅     | botocore-stubs                               | 1.42.35         | MIT                                                 |       |
| ✅     | cffi                                         | 2.0.0           | MIT                                                 |       |
| ✅     | charset-normalizer                           | 3.4.4           | MIT                                                 |       |
| ✅     | fastapi                                      | 0.128.0         | MIT                                                 |       |
| ✅     | fastavro                                     | 1.12.1          | MIT                                                 |       |
| ✅     | fonttools                                    | 4.60.1          | MIT                                                 |       |
| ✅     | gql                                          | 3.5.3           | MIT                                                 |       |
| ✅     | graphene                                     | 3.4.3           | MIT                                                 |       |
| ✅     | httptools                                    | 0.7.1           | MIT                                                 |       |
| ✅     | httpx-sse                                    | 0.4.0           | MIT                                                 |       |
| ✅     | iniconfig                                    | 2.3.0           | MIT                                                 |       |
| ✅     | kuzu                                         | 0.11.3          | MIT                                                 |       |
| ✅     | langchain                                    | 1.2.7           | MIT                                                 |       |
| ✅     | langchain-aws                                | 1.1.0           | MIT                                                 |       |
| ✅     | langchain-classic                            | 1.0.1           | MIT                                                 |       |
| ✅     | langchain-core                               | 1.2.7           | MIT                                                 |       |
| ✅     | langchain-memgraph                           | 0.1.12          | MIT                                                 |       |
| ✅     | langchain-neo4j                              | 0.8.0           | MIT                                                 |       |
| ✅     | langchain-text-splitters                     | 1.1.0           | MIT                                                 |       |
| ✅     | langgraph                                    | 1.0.7           | MIT                                                 |       |
| ✅     | langgraph-checkpoint                         | 4.0.0           | MIT                                                 |       |
| ✅     | langgraph-prebuilt                           | 1.0.7           | MIT                                                 |       |
| ✅     | langgraph-sdk                                | 0.3.3           | MIT                                                 |       |
| ✅     | langsmith                                    | 0.6.5           | MIT                                                 |       |
| ✅     | llama-index-core                             | 0.14.12         | MIT (override)                                      |       |
| ✅     | llama-index-embeddings-openai                | 0.5.1           | MIT                                                 |       |
| ✅     | llama-index-embeddings-openai-like           | 0.2.2           | MIT (override)                                      |       |
| ✅     | llama-index-instrumentation                  | 0.4.2           | MIT (override)                                      |       |
| ✅     | llama-index-llms-openai                      | 0.6.12          | MIT (override)                                      |       |
| ✅     | llama-index-llms-openai-like                 | 0.5.3           | MIT (override)                                      |       |
| ✅     | llama-index-postprocessor-cohere-rerank      | 0.5.1           | MIT                                                 |       |
| ✅     | llama-index-readers-file                     | 0.5.6           | MIT (override)                                      |       |
| ✅     | llama-index-storage-docstore-mongodb         | 0.4.1           | MIT                                                 |       |
| ✅     | llama-index-storage-kvstore-mongodb          | 0.4.1           | MIT                                                 |       |
| ✅     | llama-index-vector-stores-milvus             | 0.9.4           | MIT (override)                                      |       |
| ✅     | llama-index-workflows                        | 2.11.6          | MIT (override)                                      |       |
| ✅     | markitdown                                   | 0.1.4           | MIT                                                 |       |
| ✅     | mypy-boto3-s3                                | 1.42.21         | MIT                                                 |       |
| ✅     | mypy_extensions                              | 1.1.0           | MIT (override)                                      |       |
| ✅     | platformdirs                                 | 4.5.0           | MIT                                                 |       |
| ✅     | pydantic                                     | 2.12.4          | MIT                                                 |       |
| ✅     | pydantic-settings                            | 2.11.0          | MIT                                                 |       |
| ✅     | pydantic_core                                | 2.41.5          | MIT                                                 |       |
| ✅     | pyparsing                                    | 3.2.5           | MIT                                                 |       |
| ✅     | pytest-cov                                   | 6.3.0           | MIT                                                 |       |
| ✅     | soupsieve                                    | 2.8             | MIT                                                 |       |
| ✅     | types-s3transfer                             | 0.16.0          | MIT                                                 |       |
| ✅     | typing-inspection                            | 0.4.2           | MIT (override)                                      |       |
| ✅     | universal_pathlib                            | 0.3.4           | MIT                                                 |       |
| ✅     | urllib3                                      | 2.5.0           | MIT (override)                                      |       |
| ✅     | zipp                                         | 3.23.0          | MIT (override)                                      |       |
| ✅     | pillow                                       | 12.0.0          | MIT-CMU (override)                                  |       |
| ✅     | certifi                                      | 2025.10.5       | Mozilla Public License 2.0 (MPL 2.0)                |       |
| ✅     | pathspec                                     | 0.12.1          | Mozilla Public License 2.0 (MPL 2.0)                |       |
| ✅     | typing_extensions                            | 4.15.0          | PSF-2.0 (override)                                  |       |
| ✅     | aiohappyeyeballs                             | 2.6.1           | Python Software Foundation License                  |       |
| ✅     | defusedxml                                   | 0.7.1           | Python Software Foundation License                  |       |
| ✅     | matplotlib                                   | 3.10.7          | Python Software Foundation License                  |       |
| ✅     | pathlib_abc                                  | 0.5.2           | Python Software Foundation License                  |       |
| ✅     | filelock                                     | 3.20.0          | Unlicense                                           |       |

## JavaScript/TypeScript Dependencies

### aihub_web (Node.js)

| Status | Package                                            | Version       | License                                       | Notes                                                                                  |
| ------ | -------------------------------------------------- | ------------- | --------------------------------------------- | -------------------------------------------------------------------------------------- |
| ✅     | @babel/code-frame                                  | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/compat-data                                 | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/core                                        | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/generator                                   | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-annotate-as-pure                     | 7.27.3        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-compilation-targets                  | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-create-class-features-plugin         | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-globals                              | 7.28.0        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-member-expression-to-functions       | 7.28.5        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-module-imports                       | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-module-transforms                    | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-optimise-call-expression             | 7.27.1        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-plugin-utils                         | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-replace-supers                       | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-skip-transparent-expression-wrappers | 7.27.1        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-string-parser                        | 7.27.1        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-validator-identifier                 | 7.28.5        | MIT                                           |                                                                                        |
| ✅     | @babel/helper-validator-option                     | 7.27.1        | MIT                                           |                                                                                        |
| ✅     | @babel/helpers                                     | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/parser                                      | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/plugin-syntax-jsx                           | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/plugin-syntax-typescript                    | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/plugin-transform-typescript                 | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/standalone                                  | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/template                                    | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/traverse                                    | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @babel/types                                       | 7.28.6        | MIT                                           |                                                                                        |
| ✅     | @bomb.sh/tab                                       | 0.0.11        | MIT                                           |                                                                                        |
| ✅     | @clack/core                                        | 1.0.0-alpha.7 | MIT                                           |                                                                                        |
| ✅     | @clack/prompts                                     | 1.0.0-alpha.9 | MIT                                           |                                                                                        |
| ✅     | @cloudflare/kv-asset-handler                       | 0.4.2         | MIT OR Apache-2.0                             |                                                                                        |
| ✅     | @dagrejs/dagre                                     | 1.1.8         | MIT                                           |                                                                                        |
| ✅     | @dagrejs/graphlib                                  | 2.2.4         | MIT                                           |                                                                                        |
| ✅     | @dxup/nuxt                                         | 0.3.2         | MIT                                           |                                                                                        |
| ✅     | @dxup/unimport                                     | 0.1.2         | MIT                                           |                                                                                        |
| ✅     | @esbuild/linux-x64                                 | 0.27.2        | MIT                                           |                                                                                        |
| ✅     | @eslint-community/eslint-utils                     | 4.9.1         | MIT                                           |                                                                                        |
| ✅     | @eslint-community/regexpp                          | 4.12.2        | MIT                                           |                                                                                        |
| ✅     | @eslint/config-array                               | 0.21.1        | Apache-2.0                                    |                                                                                        |
| ✅     | @eslint/config-helpers                             | 0.4.2         | Apache-2.0                                    |                                                                                        |
| ✅     | @eslint/core                                       | 0.17.0        | Apache-2.0                                    |                                                                                        |
| ✅     | @eslint/eslintrc                                   | 3.3.3         | MIT                                           |                                                                                        |
| ✅     | @eslint/js                                         | 9.39.2        | MIT                                           |                                                                                        |
| ✅     | @eslint/object-schema                              | 2.1.7         | Apache-2.0                                    |                                                                                        |
| ✅     | @eslint/plugin-kit                                 | 0.4.1         | Apache-2.0                                    |                                                                                        |
| ✅     | @floating-ui/core                                  | 1.7.4         | MIT                                           |                                                                                        |
| ✅     | @floating-ui/dom                                   | 1.7.5         | MIT                                           |                                                                                        |
| ✅     | @floating-ui/utils                                 | 0.2.10        | MIT                                           |                                                                                        |
| ✅     | @floating-ui/vue                                   | 1.1.10        | MIT                                           |                                                                                        |
| ✅     | @hey-api/codegen-core                              | 0.5.5         | MIT                                           |                                                                                        |
| ✅     | @hey-api/json-schema-ref-parser                    | 1.2.2         | MIT                                           |                                                                                        |
| ✅     | @hey-api/nuxt                                      | 0.2.1         | MIT                                           |                                                                                        |
| ✅     | @hey-api/openapi-ts                                | 0.90.10       | MIT                                           |                                                                                        |
| ✅     | @hey-api/types                                     | 0.1.2         | MIT                                           |                                                                                        |
| ✅     | @humanfs/core                                      | 0.19.1        | Apache-2.0                                    |                                                                                        |
| ✅     | @humanfs/node                                      | 0.16.7        | Apache-2.0                                    |                                                                                        |
| ✅     | @humanwhocodes/module-importer                     | 1.0.1         | Apache-2.0                                    |                                                                                        |
| ✅     | @humanwhocodes/retry                               | 0.4.3         | Apache-2.0                                    |                                                                                        |
| ✅     | @internationalized/date                            | 3.10.1        | Apache-2.0                                    |                                                                                        |
| ✅     | @internationalized/number                          | 3.6.5         | Apache-2.0                                    |                                                                                        |
| ✅     | @ioredis/commands                                  | 1.5.0         | MIT                                           |                                                                                        |
| ✅     | @isaacs/balanced-match                             | 4.0.1         | MIT                                           |                                                                                        |
| ✅     | @isaacs/brace-expansion                            | 5.0.0         | MIT                                           |                                                                                        |
| ✅     | @isaacs/cliui                                      | 8.0.2         | ISC                                           |                                                                                        |
| ✅     | @isaacs/fs-minipass                                | 4.0.1         | ISC                                           |                                                                                        |
| ✅     | @jridgewell/gen-mapping                            | 0.3.13        | MIT                                           |                                                                                        |
| ✅     | @jridgewell/remapping                              | 2.3.5         | MIT                                           |                                                                                        |
| ✅     | @jridgewell/resolve-uri                            | 3.1.2         | MIT                                           |                                                                                        |
| ✅     | @jridgewell/source-map                             | 0.3.11        | MIT                                           |                                                                                        |
| ✅     | @jridgewell/sourcemap-codec                        | 1.5.5         | MIT                                           |                                                                                        |
| ✅     | @jridgewell/trace-mapping                          | 0.3.31        | MIT                                           |                                                                                        |
| ✅     | @jsdevtools/ono                                    | 7.1.3         | MIT                                           |                                                                                        |
| ✅     | @kwsites/file-exists                               | 1.1.1         | MIT                                           |                                                                                        |
| ✅     | @kwsites/promise-deferred                          | 1.1.1         | MIT                                           |                                                                                        |
| ✅     | @mapbox/node-pre-gyp                               | 2.0.3         | BSD-3-Clause                                  |                                                                                        |
| ✅     | @nodelib/fs.scandir                                | 2.1.5         | MIT                                           |                                                                                        |
| ✅     | @nodelib/fs.stat                                   | 2.0.5         | MIT                                           |                                                                                        |
| ✅     | @nodelib/fs.walk                                   | 1.2.8         | MIT                                           |                                                                                        |
| ✅     | @nuxt/cli                                          | 3.32.0        | MIT                                           |                                                                                        |
| ✅     | @nuxt/devalue                                      | 2.0.2         | MIT                                           |                                                                                        |
| ✅     | @nuxt/devtools                                     | 3.1.1         | MIT                                           |                                                                                        |
| ✅     | @nuxt/devtools-kit                                 | 3.1.1         | MIT                                           |                                                                                        |
| ✅     | @nuxt/devtools-wizard                              | 3.1.1         | MIT                                           |                                                                                        |
| ✅     | @nuxt/kit                                          | 3.15.4        | MIT                                           |                                                                                        |
| ✅     | @nuxt/nitro-server                                 | 3.21.0        | MIT                                           |                                                                                        |
| ✅     | @nuxt/schema                                       | 3.21.0        | MIT                                           |                                                                                        |
| ✅     | @nuxt/telemetry                                    | 2.6.6         | MIT                                           |                                                                                        |
| ✅     | @nuxt/vite-builder                                 | 3.21.0        | MIT                                           |                                                                                        |
| ✅     | @oxc-minify/binding-linux-x64-gnu                  | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @oxc-minify/binding-linux-x64-musl                 | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @oxc-parser/binding-linux-x64-gnu                  | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @oxc-parser/binding-linux-x64-musl                 | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @oxc-project/types                                 | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @oxc-transform/binding-linux-x64-gnu               | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @oxc-transform/binding-linux-x64-musl              | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | @parcel/watcher                                    | 2.5.6         | MIT                                           |                                                                                        |
| ✅     | @parcel/watcher-linux-x64-glibc                    | 2.5.6         | MIT                                           |                                                                                        |
| ✅     | @parcel/watcher-linux-x64-musl                     | 2.5.6         | MIT                                           |                                                                                        |
| ✅     | @parcel/watcher-wasm                               | 2.5.6         | MIT                                           |                                                                                        |
| ✅     | @pinia/colada                                      | 0.17.9        | MIT                                           |                                                                                        |
| ✅     | @pinia/colada-nuxt                                 | 0.2.6         | MIT                                           |                                                                                        |
| ✅     | @pinia/nuxt                                        | 0.11.3        | MIT                                           |                                                                                        |
| ✅     | @pkgjs/parseargs                                   | 0.11.0        | MIT                                           |                                                                                        |
| ✅     | @polka/url                                         | 1.0.0-next.29 | MIT                                           |                                                                                        |
| ✅     | @poppinss/colors                                   | 4.1.6         | MIT                                           |                                                                                        |
| ✅     | @poppinss/dumper                                   | 0.6.5         | MIT                                           |                                                                                        |
| ✅     | @poppinss/exception                                | 1.2.3         | MIT                                           |                                                                                        |
| ✅     | @primeuix/forms                                    | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | @primeuix/styled                                   | 0.6.4         | MIT                                           |                                                                                        |
| ✅     | @primeuix/styles                                   | 1.2.5         | MIT                                           |                                                                                        |
| ✅     | @primeuix/themes                                   | 1.1.1         | MIT                                           |                                                                                        |
| ✅     | @primeuix/utils                                    | 0.5.4         | MIT                                           |                                                                                        |
| ✅     | @primevue/core                                     | 4.3.6         | MIT                                           |                                                                                        |
| ✅     | @primevue/forms                                    | 4.5.4         | MIT                                           |                                                                                        |
| ✅     | @primevue/icons                                    | 4.3.6         | MIT                                           |                                                                                        |
| ✅     | @rolldown/pluginutils                              | 1.0.0-beta.53 | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-alias                               | 6.0.0         | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-commonjs                            | 29.0.0        | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-inject                              | 5.0.5         | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-json                                | 6.1.0         | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-node-resolve                        | 16.0.3        | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-replace                             | 6.0.3         | MIT                                           |                                                                                        |
| ✅     | @rollup/plugin-terser                              | 0.4.4         | MIT                                           |                                                                                        |
| ✅     | @rollup/pluginutils                                | 5.3.0         | MIT                                           |                                                                                        |
| ✅     | @rollup/rollup-linux-x64-gnu                       | 4.57.0        | MIT                                           |                                                                                        |
| ✅     | @rollup/rollup-linux-x64-musl                      | 4.57.0        | MIT                                           |                                                                                        |
| ✅     | @sigma/edge-curve                                  | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | @sindresorhus/is                                   | 7.2.0         | MIT                                           |                                                                                        |
| ✅     | @sindresorhus/merge-streams                        | 2.3.0         | MIT                                           |                                                                                        |
| ✅     | @socket.io/component-emitter                       | 3.1.2         | MIT                                           |                                                                                        |
| ✅     | @speed-highlight/core                              | 1.2.14        | CC0-1.0                                       |                                                                                        |
| ✅     | @svgdotjs/svg.draggable.js                         | 3.0.6         | MIT                                           |                                                                                        |
| ✅     | @svgdotjs/svg.filter.js                            | 3.0.9         | MIT                                           |                                                                                        |
| ✅     | @svgdotjs/svg.js                                   | 3.2.5         | MIT                                           |                                                                                        |
| ✅     | @svgdotjs/svg.resize.js                            | 2.0.5         | MIT                                           |                                                                                        |
| ✅     | @svgdotjs/svg.select.js                            | 4.0.3         | MIT                                           |                                                                                        |
| ✅     | @swc/helpers                                       | 0.5.18        | Apache-2.0                                    |                                                                                        |
| ✅     | @tanstack/virtual-core                             | 3.13.18       | MIT                                           |                                                                                        |
| ✅     | @tanstack/vue-virtual                              | 3.13.18       | MIT                                           |                                                                                        |
| ✅     | @types/estree                                      | 1.0.8         | MIT                                           |                                                                                        |
| ✅     | @types/json-schema                                 | 7.0.15        | MIT                                           |                                                                                        |
| ✅     | @types/node                                        | 22.19.7       | MIT                                           |                                                                                        |
| ✅     | @types/parse-path                                  | 7.1.0         | MIT                                           |                                                                                        |
| ✅     | @types/resolve                                     | 1.20.2        | MIT                                           |                                                                                        |
| ✅     | @types/web-bluetooth                               | 0.0.20        | MIT                                           |                                                                                        |
| ✅     | @unhead/vue                                        | 2.1.2         | MIT                                           |                                                                                        |
| ✅     | @vercel/nft                                        | 1.3.0         | MIT                                           |                                                                                        |
| ✅     | @vitejs/plugin-vue                                 | 6.0.3         | MIT                                           |                                                                                        |
| ✅     | @vitejs/plugin-vue-jsx                             | 5.1.3         | MIT                                           |                                                                                        |
| ✅     | @volar/language-core                               | 2.4.27        | MIT                                           |                                                                                        |
| ✅     | @volar/source-map                                  | 2.4.27        | MIT                                           |                                                                                        |
| ✅     | @vue-flow/background                               | 1.3.2         | MIT                                           |                                                                                        |
| ✅     | @vue-flow/controls                                 | 1.1.3         | MIT                                           |                                                                                        |
| ✅     | @vue-flow/core                                     | 1.48.2        | MIT                                           |                                                                                        |
| ✅     | @vue-flow/minimap                                  | 1.5.4         | MIT                                           |                                                                                        |
| ✅     | @vue-macros/common                                 | 3.1.2         | MIT                                           |                                                                                        |
| ✅     | @vue/babel-helper-vue-transform-on                 | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | @vue/babel-plugin-jsx                              | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | @vue/babel-plugin-resolve-type                     | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | @vue/compiler-core                                 | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/compiler-dom                                  | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/compiler-sfc                                  | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/compiler-ssr                                  | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/devtools-api                                  | 6.6.4         | MIT                                           |                                                                                        |
| ✅     | @vue/devtools-core                                 | 8.0.5         | MIT                                           |                                                                                        |
| ✅     | @vue/devtools-kit                                  | 7.7.9         | MIT                                           |                                                                                        |
| ✅     | @vue/devtools-shared                               | 7.7.9         | MIT                                           |                                                                                        |
| ✅     | @vue/language-core                                 | 3.2.4         | MIT                                           |                                                                                        |
| ✅     | @vue/reactivity                                    | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/runtime-core                                  | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/runtime-dom                                   | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/server-renderer                               | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vue/shared                                        | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | @vueuse/core                                       | 10.11.1       | MIT                                           |                                                                                        |
| ✅     | @vueuse/integrations                               | 13.9.0        | MIT                                           |                                                                                        |
| ✅     | @vueuse/math                                       | 13.9.0        | MIT                                           |                                                                                        |
| ✅     | @vueuse/metadata                                   | 10.11.1       | MIT                                           |                                                                                        |
| ✅     | @vueuse/router                                     | 13.9.0        | MIT                                           |                                                                                        |
| ✅     | @vueuse/shared                                     | 10.11.1       | MIT                                           |                                                                                        |
| ✅     | @yr/monotone-cubic-spline                          | 1.0.3         | MIT                                           |                                                                                        |
| ✅     | abbrev                                             | 3.0.1         | ISC                                           |                                                                                        |
| ✅     | abort-controller                                   | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | acorn                                              | 8.15.0        | MIT                                           |                                                                                        |
| ✅     | acorn-import-attributes                            | 1.9.5         | MIT                                           |                                                                                        |
| ✅     | acorn-jsx                                          | 5.3.2         | MIT                                           |                                                                                        |
| ✅     | agent-base                                         | 7.1.4         | MIT                                           |                                                                                        |
| ✅     | ajv                                                | 6.12.6        | MIT                                           |                                                                                        |
| ✅     | alien-signals                                      | 3.1.2         | MIT                                           |                                                                                        |
| ✅     | ansi-colors                                        | 4.1.3         | MIT                                           |                                                                                        |
| ✅     | ansi-regex                                         | 5.0.1         | MIT                                           |                                                                                        |
| ✅     | ansi-styles                                        | 4.3.0         | MIT                                           |                                                                                        |
| ✅     | ansis                                              | 4.2.0         | ISC                                           |                                                                                        |
| ✅     | anymatch                                           | 3.1.3         | ISC                                           |                                                                                        |
| ✅     | apexcharts                                         | 4.7.0         | MIT                                           |                                                                                        |
| ✅     | archiver                                           | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | archiver-utils                                     | 5.0.2         | MIT                                           |                                                                                        |
| ✅     | argparse                                           | 2.0.1         | Python Software Foundation License (override) |                                                                                        |
| ✅     | aria-hidden                                        | 1.2.6         | MIT                                           |                                                                                        |
| ✅     | ast-kit                                            | 2.2.0         | MIT                                           |                                                                                        |
| ✅     | ast-walker-scope                                   | 0.8.3         | MIT                                           |                                                                                        |
| ✅     | async                                              | 3.2.6         | MIT                                           |                                                                                        |
| ✅     | async-sema                                         | 3.1.1         | MIT                                           |                                                                                        |
| ✅     | autoprefixer                                       | 10.4.23       | MIT                                           |                                                                                        |
| ✅     | b4a                                                | 1.7.3         | Apache-2.0                                    |                                                                                        |
| ✅     | balanced-match                                     | 1.0.2         | MIT                                           |                                                                                        |
| ✅     | bare-events                                        | 2.8.2         | Apache-2.0                                    |                                                                                        |
| ✅     | base64-js                                          | 1.5.1         | MIT                                           |                                                                                        |
| ✅     | baseline-browser-mapping                           | 2.9.19        | Apache-2.0                                    |                                                                                        |
| ✅     | bindings                                           | 1.5.0         | MIT                                           |                                                                                        |
| ✅     | birpc                                              | 2.9.0         | MIT                                           |                                                                                        |
| ✅     | boolbase                                           | 1.0.0         | ISC                                           |                                                                                        |
| ✅     | brace-expansion                                    | 1.1.12        | MIT                                           |                                                                                        |
| ✅     | braces                                             | 3.0.3         | MIT                                           |                                                                                        |
| ✅     | browserslist                                       | 4.28.1        | MIT                                           |                                                                                        |
| ✅     | buffer                                             | 6.0.3         | MIT                                           |                                                                                        |
| ✅     | buffer-crc32                                       | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | buffer-from                                        | 1.1.2         | MIT                                           |                                                                                        |
| ✅     | bundle-name                                        | 4.1.0         | MIT                                           |                                                                                        |
| ✅     | c12                                                | 2.0.4         | MIT                                           |                                                                                        |
| ✅     | cac                                                | 6.7.14        | MIT                                           |                                                                                        |
| ✅     | callsites                                          | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | caniuse-api                                        | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | caniuse-lite                                       | 1.0.30001766  | CC-BY-4.0                                     |                                                                                        |
| ✅     | chalk                                              | 4.1.2         | MIT                                           |                                                                                        |
| ✅     | change-case                                        | 5.4.4         | MIT                                           |                                                                                        |
| ✅     | chokidar                                           | 4.0.3         | MIT                                           |                                                                                        |
| ✅     | chownr                                             | 2.0.0         | ISC                                           |                                                                                        |
| ✅     | chownr                                             | 3.0.0         | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | citty                                              | 0.1.6         | MIT                                           |                                                                                        |
| ✅     | class-variance-authority                           | 0.7.1         | Apache-2.0                                    |                                                                                        |
| ✅     | clipboardy                                         | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | cliui                                              | 8.0.1         | ISC                                           |                                                                                        |
| ✅     | clsx                                               | 2.1.1         | MIT                                           |                                                                                        |
| ✅     | cluster-key-slot                                   | 1.1.2         | Apache-2.0                                    |                                                                                        |
| ✅     | color-convert                                      | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | color-name                                         | 1.1.4         | MIT                                           |                                                                                        |
| ✅     | color-support                                      | 1.1.3         | ISC                                           |                                                                                        |
| ✅     | colord                                             | 2.9.3         | MIT                                           |                                                                                        |
| ✅     | commander                                          | 2.20.3        | MIT                                           |                                                                                        |
| ✅     | commondir                                          | 1.0.1         | MIT                                           |                                                                                        |
| ✅     | compatx                                            | 0.2.0         | MIT                                           |                                                                                        |
| ✅     | compress-commons                                   | 6.0.2         | MIT                                           |                                                                                        |
| ✅     | concat-map                                         | 0.0.1         | MIT                                           |                                                                                        |
| ✅     | confbox                                            | 0.1.8         | MIT                                           |                                                                                        |
| ✅     | consola                                            | 3.4.2         | MIT                                           |                                                                                        |
| ✅     | convert-source-map                                 | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | cookie-es                                          | 1.2.2         | MIT                                           |                                                                                        |
| ✅     | copy-anything                                      | 4.0.5         | MIT                                           |                                                                                        |
| ✅     | copy-paste                                         | 2.2.0         | MIT                                           | MIT license per package.json; npm reports Unknown due to missing SPDX in older format. |
| ✅     | core-util-is                                       | 1.0.3         | MIT                                           |                                                                                        |
| ✅     | crc-32                                             | 1.2.2         | Apache-2.0                                    |                                                                                        |
| ✅     | crc32-stream                                       | 6.0.0         | MIT                                           |                                                                                        |
| ✅     | croner                                             | 9.1.0         | MIT                                           |                                                                                        |
| ✅     | cross-spawn                                        | 7.0.6         | MIT                                           |                                                                                        |
| ✅     | crossws                                            | 0.3.5         | MIT                                           |                                                                                        |
| ✅     | css-declaration-sorter                             | 7.3.1         | ISC                                           |                                                                                        |
| ✅     | css-select                                         | 5.2.2         | BSD-2-Clause                                  |                                                                                        |
| ✅     | css-tree                                           | 2.2.1         | MIT                                           |                                                                                        |
| ✅     | css-what                                           | 6.2.2         | BSD-2-Clause                                  |                                                                                        |
| ✅     | cssesc                                             | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | cssnano                                            | 7.1.2         | MIT                                           |                                                                                        |
| ✅     | cssnano-preset-default                             | 7.0.10        | MIT                                           |                                                                                        |
| ✅     | cssnano-utils                                      | 5.0.1         | MIT                                           |                                                                                        |
| ✅     | csso                                               | 5.0.5         | MIT                                           |                                                                                        |
| ✅     | csstype                                            | 3.2.3         | MIT                                           |                                                                                        |
| ✅     | d3-color                                           | 3.1.0         | ISC                                           |                                                                                        |
| ✅     | d3-dispatch                                        | 3.0.1         | ISC                                           |                                                                                        |
| ✅     | d3-drag                                            | 3.0.0         | ISC                                           |                                                                                        |
| ✅     | d3-ease                                            | 3.0.1         | BSD-3-Clause                                  |                                                                                        |
| ✅     | d3-interpolate                                     | 3.0.1         | ISC                                           |                                                                                        |
| ✅     | d3-selection                                       | 3.0.0         | ISC                                           |                                                                                        |
| ✅     | d3-timer                                           | 3.0.1         | ISC                                           |                                                                                        |
| ✅     | d3-transition                                      | 3.0.1         | ISC                                           |                                                                                        |
| ✅     | d3-zoom                                            | 3.0.0         | ISC                                           |                                                                                        |
| ✅     | date-fns                                           | 4.1.0         | MIT                                           |                                                                                        |
| ✅     | db0                                                | 0.3.4         | MIT                                           |                                                                                        |
| ✅     | debug                                              | 4.4.3         | MIT                                           |                                                                                        |
| ✅     | deep-is                                            | 0.1.4         | MIT                                           |                                                                                        |
| ✅     | deepmerge                                          | 4.3.1         | MIT                                           |                                                                                        |
| ✅     | default-browser                                    | 5.4.0         | MIT                                           |                                                                                        |
| ✅     | default-browser-id                                 | 5.0.1         | MIT                                           |                                                                                        |
| ✅     | define-lazy-prop                                   | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | defu                                               | 6.1.4         | MIT                                           |                                                                                        |
| ✅     | denque                                             | 2.1.0         | Apache-2.0                                    |                                                                                        |
| ✅     | depd                                               | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | destr                                              | 2.0.5         | MIT                                           |                                                                                        |
| ✅     | detect-libc                                        | 2.1.2         | Apache-2.0                                    |                                                                                        |
| ✅     | devalue                                            | 5.6.2         | MIT                                           |                                                                                        |
| ✅     | diff                                               | 8.0.3         | BSD-3-Clause                                  |                                                                                        |
| ✅     | dom-serializer                                     | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | domelementtype                                     | 2.3.0         | BSD-2-Clause                                  |                                                                                        |
| ✅     | domhandler                                         | 5.0.3         | BSD-2-Clause                                  |                                                                                        |
| ✅     | domutils                                           | 3.2.2         | BSD-2-Clause                                  |                                                                                        |
| ✅     | dot-prop                                           | 10.1.0        | MIT                                           |                                                                                        |
| ✅     | dotenv                                             | 16.6.1        | BSD-2-Clause                                  |                                                                                        |
| ✅     | duplexer                                           | 0.1.2         | MIT                                           |                                                                                        |
| ✅     | eastasianwidth                                     | 0.2.0         | MIT                                           |                                                                                        |
| ✅     | ee-first                                           | 1.1.1         | MIT                                           |                                                                                        |
| ✅     | electron-to-chromium                               | 1.5.282       | ISC                                           |                                                                                        |
| ✅     | emoji-regex                                        | 8.0.0         | MIT                                           |                                                                                        |
| ✅     | encodeurl                                          | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | engine.io-client                                   | 6.6.4         | MIT                                           |                                                                                        |
| ✅     | engine.io-parser                                   | 5.2.3         | MIT                                           |                                                                                        |
| ✅     | enhanced-resolve                                   | 5.18.4        | MIT                                           |                                                                                        |
| ✅     | entities                                           | 4.5.0         | BSD-2-Clause                                  |                                                                                        |
| ✅     | error-stack-parser-es                              | 1.0.5         | MIT                                           |                                                                                        |
| ✅     | errx                                               | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | es-module-lexer                                    | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | esbuild                                            | 0.27.2        | MIT                                           |                                                                                        |
| ✅     | escalade                                           | 3.2.0         | MIT                                           |                                                                                        |
| ✅     | escape-html                                        | 1.0.3         | MIT                                           |                                                                                        |
| ✅     | escape-string-regexp                               | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | eslint                                             | 9.39.2        | MIT                                           |                                                                                        |
| ✅     | eslint-scope                                       | 8.4.0         | BSD-2-Clause                                  |                                                                                        |
| ✅     | eslint-visitor-keys                                | 3.4.3         | Apache-2.0                                    |                                                                                        |
| ✅     | espree                                             | 10.4.0        | BSD-2-Clause                                  |                                                                                        |
| ✅     | esquery                                            | 1.7.0         | BSD-3-Clause                                  |                                                                                        |
| ✅     | esrecurse                                          | 4.3.0         | BSD-2-Clause                                  |                                                                                        |
| ✅     | estraverse                                         | 5.3.0         | BSD-2-Clause                                  |                                                                                        |
| ✅     | estree-walker                                      | 2.0.2         | MIT                                           |                                                                                        |
| ✅     | esutils                                            | 2.0.3         | BSD-2-Clause                                  |                                                                                        |
| ✅     | etag                                               | 1.8.1         | MIT                                           |                                                                                        |
| ✅     | event-target-shim                                  | 5.0.1         | MIT                                           |                                                                                        |
| ✅     | eventemitter3                                      | 5.0.4         | MIT                                           |                                                                                        |
| ✅     | events                                             | 3.3.0         | MIT                                           |                                                                                        |
| ✅     | events-universal                                   | 1.0.1         | Apache-2.0                                    |                                                                                        |
| ✅     | execa                                              | 8.0.1         | MIT                                           |                                                                                        |
| ✅     | exsolve                                            | 1.0.8         | MIT                                           |                                                                                        |
| ✅     | externality                                        | 1.0.2         | MIT                                           |                                                                                        |
| ✅     | fast-deep-equal                                    | 3.1.3         | MIT                                           |                                                                                        |
| ✅     | fast-diff                                          | 1.3.0         | Apache-2.0                                    |                                                                                        |
| ✅     | fast-fifo                                          | 1.3.2         | MIT                                           |                                                                                        |
| ✅     | fast-glob                                          | 3.3.3         | MIT                                           |                                                                                        |
| ✅     | fast-json-stable-stringify                         | 2.1.0         | MIT                                           |                                                                                        |
| ✅     | fast-levenshtein                                   | 2.0.6         | MIT                                           |                                                                                        |
| ✅     | fast-npm-meta                                      | 0.4.8         | MIT                                           |                                                                                        |
| ✅     | fastq                                              | 1.20.1        | ISC                                           |                                                                                        |
| ✅     | fdir                                               | 6.5.0         | MIT                                           |                                                                                        |
| ✅     | file-entry-cache                                   | 8.0.0         | MIT                                           |                                                                                        |
| ✅     | file-uri-to-path                                   | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | fill-range                                         | 7.1.1         | MIT                                           |                                                                                        |
| ✅     | find-up                                            | 5.0.0         | MIT                                           |                                                                                        |
| ✅     | flat-cache                                         | 4.0.1         | MIT                                           |                                                                                        |
| ✅     | flatted                                            | 3.3.3         | ISC                                           |                                                                                        |
| ✅     | foreground-child                                   | 3.3.1         | ISC                                           |                                                                                        |
| ✅     | fraction.js                                        | 5.3.4         | MIT                                           |                                                                                        |
| ✅     | fresh                                              | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | fs-minipass                                        | 2.1.0         | ISC                                           |                                                                                        |
| ✅     | function-bind                                      | 1.1.2         | MIT                                           |                                                                                        |
| ✅     | fuse.js                                            | 7.1.0         | Apache-2.0                                    |                                                                                        |
| ✅     | gensync                                            | 1.0.0-beta.2  | MIT                                           |                                                                                        |
| ✅     | get-caller-file                                    | 2.0.5         | ISC                                           |                                                                                        |
| ✅     | get-port-please                                    | 3.2.0         | MIT                                           |                                                                                        |
| ✅     | get-stream                                         | 8.0.1         | MIT                                           |                                                                                        |
| ✅     | giget                                              | 1.2.5         | MIT                                           |                                                                                        |
| ✅     | git-up                                             | 8.1.1         | MIT                                           |                                                                                        |
| ✅     | git-url-parse                                      | 16.1.0        | MIT                                           |                                                                                        |
| ✅     | glob                                               | 10.5.0        | ISC                                           |                                                                                        |
| ✅     | glob                                               | 13.0.0        | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | glob-parent                                        | 5.1.2         | ISC                                           |                                                                                        |
| ✅     | global-directory                                   | 4.0.1         | MIT                                           |                                                                                        |
| ✅     | globals                                            | 14.0.0        | MIT                                           |                                                                                        |
| ✅     | globby                                             | 14.1.0        | MIT                                           |                                                                                        |
| ✅     | graceful-fs                                        | 4.2.11        | ISC                                           |                                                                                        |
| ✅     | graphology                                         | 0.26.0        | MIT                                           |                                                                                        |
| ✅     | graphology-layout-forceatlas2                      | 0.10.1        | MIT                                           |                                                                                        |
| ✅     | graphology-types                                   | 0.24.8        | MIT                                           |                                                                                        |
| ✅     | graphology-utils                                   | 2.5.2         | MIT                                           |                                                                                        |
| ✅     | gridstack                                          | 12.4.2        | MIT                                           |                                                                                        |
| ✅     | gzip-size                                          | 7.0.0         | MIT                                           |                                                                                        |
| ✅     | h3                                                 | 1.15.5        | MIT                                           |                                                                                        |
| ✅     | has-flag                                           | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | hasown                                             | 2.0.2         | MIT                                           |                                                                                        |
| ✅     | hookable                                           | 5.5.3         | MIT                                           |                                                                                        |
| ✅     | http-errors                                        | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | http-shutdown                                      | 1.2.2         | MIT                                           |                                                                                        |
| ✅     | https-proxy-agent                                  | 7.0.6         | MIT                                           |                                                                                        |
| ✅     | httpxy                                             | 0.1.7         | MIT                                           |                                                                                        |
| ✅     | human-signals                                      | 5.0.0         | Apache-2.0                                    |                                                                                        |
| ✅     | iconv-lite                                         | 0.4.24        | MIT                                           |                                                                                        |
| ✅     | ieee754                                            | 1.2.1         | BSD-3-Clause                                  |                                                                                        |
| ✅     | ignore                                             | 5.3.2         | MIT                                           |                                                                                        |
| ✅     | image-meta                                         | 0.2.2         | MIT                                           |                                                                                        |
| ✅     | import-fresh                                       | 3.3.1         | MIT                                           |                                                                                        |
| ✅     | impound                                            | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | imurmurhash                                        | 0.1.4         | MIT                                           |                                                                                        |
| ✅     | inherits                                           | 2.0.4         | ISC                                           |                                                                                        |
| ✅     | ini                                                | 4.1.1         | ISC                                           |                                                                                        |
| ✅     | ioredis                                            | 5.9.2         | MIT                                           |                                                                                        |
| ✅     | iron-webcrypto                                     | 1.2.1         | MIT                                           |                                                                                        |
| ✅     | is-core-module                                     | 2.16.1        | MIT                                           |                                                                                        |
| ✅     | is-docker                                          | 2.2.1         | MIT                                           |                                                                                        |
| ✅     | is-extglob                                         | 2.1.1         | MIT                                           |                                                                                        |
| ✅     | is-fullwidth-code-point                            | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | is-glob                                            | 4.0.3         | MIT                                           |                                                                                        |
| ✅     | is-in-ssh                                          | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | is-inside-container                                | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | is-installed-globally                              | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | is-module                                          | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | is-number                                          | 7.0.0         | MIT                                           |                                                                                        |
| ✅     | is-path-inside                                     | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | is-reference                                       | 1.2.1         | MIT                                           |                                                                                        |
| ✅     | is-ssh                                             | 1.4.1         | MIT                                           |                                                                                        |
| ✅     | is-stream                                          | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | is-what                                            | 5.5.0         | MIT                                           |                                                                                        |
| ✅     | is-wsl                                             | 2.2.0         | MIT                                           |                                                                                        |
| ✅     | is64bit                                            | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | isarray                                            | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | isexe                                              | 2.0.0         | ISC                                           |                                                                                        |
| ✅     | jackspeak                                          | 3.4.3         | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | jiti                                               | 1.21.7        | MIT                                           |                                                                                        |
| ✅     | js-tokens                                          | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | js-yaml                                            | 4.1.1         | MIT                                           |                                                                                        |
| ✅     | jsesc                                              | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | json-buffer                                        | 3.0.1         | MIT                                           |                                                                                        |
| ✅     | json-schema-traverse                               | 0.4.1         | MIT                                           |                                                                                        |
| ✅     | json-stable-stringify-without-jsonify              | 1.0.1         | MIT                                           |                                                                                        |
| ✅     | json5                                              | 2.2.3         | MIT                                           |                                                                                        |
| ✅     | jwt-decode                                         | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | keyv                                               | 4.5.4         | MIT                                           |                                                                                        |
| ✅     | kleur                                              | 3.0.3         | MIT                                           |                                                                                        |
| ✅     | klona                                              | 2.0.6         | MIT                                           |                                                                                        |
| ✅     | knitwork                                           | 1.3.0         | MIT                                           |                                                                                        |
| ✅     | launch-editor                                      | 2.12.0        | MIT                                           |                                                                                        |
| ✅     | lazystream                                         | 1.0.1         | MIT                                           |                                                                                        |
| ✅     | levn                                               | 0.4.1         | MIT                                           |                                                                                        |
| ✅     | lilconfig                                          | 3.1.3         | MIT                                           |                                                                                        |
| ✅     | listhen                                            | 1.9.0         | MIT                                           |                                                                                        |
| ✅     | local-pkg                                          | 1.1.2         | MIT                                           |                                                                                        |
| ✅     | locate-path                                        | 6.0.0         | MIT                                           |                                                                                        |
| ✅     | lodash                                             | 4.17.23       | MIT                                           |                                                                                        |
| ✅     | lodash-es                                          | 4.17.23       | MIT                                           |                                                                                        |
| ✅     | lodash.clonedeep                                   | 4.5.0         | MIT                                           |                                                                                        |
| ✅     | lodash.defaults                                    | 4.2.0         | MIT                                           |                                                                                        |
| ✅     | lodash.isarguments                                 | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | lodash.isequal                                     | 4.5.0         | MIT                                           |                                                                                        |
| ✅     | lodash.memoize                                     | 4.1.2         | MIT                                           |                                                                                        |
| ✅     | lodash.merge                                       | 4.6.2         | MIT                                           |                                                                                        |
| ✅     | lodash.uniq                                        | 4.5.0         | MIT                                           |                                                                                        |
| ✅     | lru-cache                                          | 11.2.5        | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | lru-cache                                          | 5.1.1         | ISC                                           |                                                                                        |
| ✅     | lucide-vue-next                                    | 0.513.0       | ISC                                           |                                                                                        |
| ✅     | magic-regexp                                       | 0.10.0        | MIT                                           |                                                                                        |
| ✅     | magic-string                                       | 0.30.21       | MIT                                           |                                                                                        |
| ✅     | magic-string-ast                                   | 1.0.3         | MIT                                           |                                                                                        |
| ✅     | magicast                                           | 0.5.1         | MIT                                           |                                                                                        |
| ✅     | mdn-data                                           | 2.0.28        | CC0-1.0                                       |                                                                                        |
| ✅     | merge-stream                                       | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | merge2                                             | 1.4.1         | MIT                                           |                                                                                        |
| ✅     | micromatch                                         | 4.0.8         | MIT                                           |                                                                                        |
| ✅     | mime                                               | 4.1.0         | MIT                                           |                                                                                        |
| ✅     | mime-db                                            | 1.54.0        | MIT                                           |                                                                                        |
| ✅     | mime-types                                         | 3.0.2         | MIT                                           |                                                                                        |
| ✅     | mimic-fn                                           | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | minimatch                                          | 10.1.1        | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | minimatch                                          | 3.1.2         | ISC                                           |                                                                                        |
| ✅     | minipass                                           | 3.3.6         | ISC                                           |                                                                                        |
| ✅     | minizlib                                           | 2.1.2         | MIT                                           |                                                                                        |
| ✅     | mitt                                               | 3.0.1         | MIT                                           |                                                                                        |
| ✅     | mkdirp                                             | 1.0.4         | MIT                                           |                                                                                        |
| ✅     | mlly                                               | 1.7.4         | MIT                                           |                                                                                        |
| ✅     | mocked-exports                                     | 0.1.1         | MIT                                           |                                                                                        |
| ✅     | mrmime                                             | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | ms                                                 | 2.1.3         | MIT                                           |                                                                                        |
| ✅     | muggle-string                                      | 0.4.1         | MIT                                           |                                                                                        |
| ✅     | nanoid                                             | 3.3.11        | MIT                                           |                                                                                        |
| ✅     | nanotar                                            | 0.2.0         | MIT                                           |                                                                                        |
| ✅     | natural-compare                                    | 1.4.0         | MIT                                           |                                                                                        |
| ✅     | nitropack                                          | 2.13.1        | MIT                                           |                                                                                        |
| ✅     | node-addon-api                                     | 7.1.1         | MIT                                           |                                                                                        |
| ✅     | node-fetch                                         | 2.7.0         | MIT                                           |                                                                                        |
| ✅     | node-fetch-native                                  | 1.6.7         | MIT                                           |                                                                                        |
| ✅     | node-forge                                         | 1.3.3         | (BSD-3-Clause OR GPL-2.0)                     | Dual-licensed; using under BSD-3-Clause (permissive).                                  |
| ✅     | node-gyp-build                                     | 4.8.4         | MIT                                           |                                                                                        |
| ✅     | node-mock-http                                     | 1.0.4         | MIT                                           |                                                                                        |
| ✅     | node-releases                                      | 2.0.27        | MIT                                           |                                                                                        |
| ✅     | nopt                                               | 8.1.0         | ISC                                           |                                                                                        |
| ✅     | normalize-path                                     | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | npm-run-path                                       | 5.3.0         | MIT                                           |                                                                                        |
| ✅     | nth-check                                          | 2.1.1         | BSD-2-Clause                                  |                                                                                        |
| ✅     | nuxt                                               | 3.21.0        | MIT                                           |                                                                                        |
| ✅     | nypm                                               | 0.5.4         | MIT                                           |                                                                                        |
| ✅     | obug                                               | 2.1.1         | MIT                                           |                                                                                        |
| ✅     | ofetch                                             | 1.5.1         | MIT                                           |                                                                                        |
| ✅     | ohash                                              | 1.1.6         | MIT                                           |                                                                                        |
| ✅     | oidc-client-ts                                     | 3.4.1         | Apache-2.0                                    |                                                                                        |
| ✅     | on-change                                          | 6.0.1         | MIT                                           |                                                                                        |
| ✅     | on-finished                                        | 2.4.1         | MIT                                           |                                                                                        |
| ✅     | onetime                                            | 6.0.0         | MIT                                           |                                                                                        |
| ✅     | open                                               | 8.4.2         | MIT                                           |                                                                                        |
| ✅     | optionator                                         | 0.9.4         | MIT                                           |                                                                                        |
| ✅     | oxc-minify                                         | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | oxc-parser                                         | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | oxc-transform                                      | 0.110.0       | MIT                                           |                                                                                        |
| ✅     | oxc-walker                                         | 0.7.0         | MIT                                           |                                                                                        |
| ✅     | p-limit                                            | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | p-locate                                           | 5.0.0         | MIT                                           |                                                                                        |
| ✅     | package-json-from-dist                             | 1.0.1         | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | package-manager-detector                           | 1.6.0         | MIT                                           |                                                                                        |
| ✅     | parchment                                          | 3.0.0         | BSD-3-Clause                                  |                                                                                        |
| ✅     | parent-module                                      | 1.0.1         | MIT                                           |                                                                                        |
| ✅     | parse-path                                         | 7.1.0         | MIT                                           |                                                                                        |
| ✅     | parse-url                                          | 9.2.0         | MIT                                           |                                                                                        |
| ✅     | parseurl                                           | 1.3.3         | MIT                                           |                                                                                        |
| ✅     | path-browserify                                    | 1.0.1         | MIT                                           |                                                                                        |
| ✅     | path-exists                                        | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | path-key                                           | 3.1.1         | MIT                                           |                                                                                        |
| ✅     | path-parse                                         | 1.0.7         | MIT                                           |                                                                                        |
| ✅     | path-scurry                                        | 1.11.1        | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | path-type                                          | 6.0.0         | MIT                                           |                                                                                        |
| ✅     | pathe                                              | 1.1.2         | MIT                                           |                                                                                        |
| ✅     | perfect-debounce                                   | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | picocolors                                         | 1.1.1         | ISC                                           |                                                                                        |
| ✅     | picomatch                                          | 2.3.1         | MIT                                           |                                                                                        |
| ✅     | pinia                                              | 3.0.4         | MIT                                           |                                                                                        |
| ✅     | pkg-types                                          | 1.3.1         | MIT                                           |                                                                                        |
| ✅     | postcss                                            | 8.5.6         | MIT                                           |                                                                                        |
| ✅     | postcss-calc                                       | 10.1.1        | MIT                                           |                                                                                        |
| ✅     | postcss-colormin                                   | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-convert-values                             | 7.0.8         | MIT                                           |                                                                                        |
| ✅     | postcss-discard-comments                           | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-discard-duplicates                         | 7.0.2         | MIT                                           |                                                                                        |
| ✅     | postcss-discard-empty                              | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-discard-overridden                         | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-merge-longhand                             | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-merge-rules                                | 7.0.7         | MIT                                           |                                                                                        |
| ✅     | postcss-minify-font-values                         | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-minify-gradients                           | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-minify-params                              | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-minify-selectors                           | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-charset                          | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-display-values                   | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-positions                        | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-repeat-style                     | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-string                           | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-timing-functions                 | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-unicode                          | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-url                              | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-normalize-whitespace                       | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-ordered-values                             | 7.0.2         | MIT                                           |                                                                                        |
| ✅     | postcss-reduce-initial                             | 7.0.5         | MIT                                           |                                                                                        |
| ✅     | postcss-reduce-transforms                          | 7.0.1         | MIT                                           |                                                                                        |
| ✅     | postcss-selector-parser                            | 7.1.1         | MIT                                           |                                                                                        |
| ✅     | postcss-svgo                                       | 7.1.0         | MIT                                           |                                                                                        |
| ✅     | postcss-unique-selectors                           | 7.0.4         | MIT                                           |                                                                                        |
| ✅     | postcss-value-parser                               | 4.2.0         | MIT                                           |                                                                                        |
| ✅     | powershell-utils                                   | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | prelude-ls                                         | 1.2.1         | MIT                                           |                                                                                        |
| ✅     | pretty-bytes                                       | 7.1.0         | MIT                                           |                                                                                        |
| ✅     | primeicons                                         | 7.0.0         | MIT                                           |                                                                                        |
| ✅     | primevue                                           | 4.3.6         | MIT                                           |                                                                                        |
| ✅     | process                                            | 0.11.10       | MIT                                           |                                                                                        |
| ✅     | process-nextick-args                               | 2.0.1         | MIT                                           |                                                                                        |
| ✅     | prompts                                            | 2.4.2         | MIT                                           |                                                                                        |
| ✅     | protocols                                          | 2.0.2         | MIT                                           |                                                                                        |
| ✅     | punycode                                           | 2.3.1         | MIT                                           |                                                                                        |
| ✅     | quansync                                           | 0.2.11        | MIT                                           |                                                                                        |
| ✅     | queue-microtask                                    | 1.2.3         | MIT                                           |                                                                                        |
| ✅     | quill                                              | 2.0.3         | BSD-3-Clause                                  |                                                                                        |
| ✅     | quill-delta                                        | 5.1.0         | MIT                                           |                                                                                        |
| ✅     | radix-vue                                          | 1.9.17        | MIT                                           |                                                                                        |
| ✅     | radix3                                             | 1.1.2         | MIT                                           |                                                                                        |
| ✅     | randombytes                                        | 2.1.0         | MIT                                           |                                                                                        |
| ✅     | range-parser                                       | 1.2.1         | MIT                                           |                                                                                        |
| ✅     | rc9                                                | 2.1.2         | MIT                                           |                                                                                        |
| ✅     | readable-stream                                    | 2.3.8         | MIT                                           |                                                                                        |
| ✅     | readdir-glob                                       | 1.1.3         | Apache-2.0                                    |                                                                                        |
| ✅     | readdirp                                           | 4.1.2         | MIT                                           |                                                                                        |
| ✅     | redis-errors                                       | 1.2.0         | MIT                                           |                                                                                        |
| ✅     | redis-parser                                       | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | regexp-tree                                        | 0.1.27        | MIT                                           |                                                                                        |
| ✅     | require-directory                                  | 2.1.1         | MIT                                           |                                                                                        |
| ✅     | resolve                                            | 1.22.11       | MIT                                           |                                                                                        |
| ✅     | resolve-from                                       | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | reusify                                            | 1.1.0         | MIT                                           |                                                                                        |
| ✅     | rfdc                                               | 1.4.1         | MIT                                           |                                                                                        |
| ✅     | rollup                                             | 4.57.0        | MIT                                           |                                                                                        |
| ✅     | rollup-plugin-visualizer                           | 6.0.5         | MIT                                           |                                                                                        |
| ✅     | rou3                                               | 0.7.12        | MIT                                           |                                                                                        |
| ✅     | run-applescript                                    | 7.1.0         | MIT                                           |                                                                                        |
| ✅     | run-parallel                                       | 1.2.0         | MIT                                           |                                                                                        |
| ✅     | safe-buffer                                        | 5.1.2         | MIT                                           |                                                                                        |
| ✅     | safer-buffer                                       | 2.1.2         | MIT                                           |                                                                                        |
| ✅     | sax                                                | 1.4.4         | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | scule                                              | 1.3.0         | MIT                                           |                                                                                        |
| ✅     | semver                                             | 6.3.1         | ISC                                           |                                                                                        |
| ✅     | send                                               | 1.2.1         | MIT                                           |                                                                                        |
| ✅     | serialize-javascript                               | 6.0.2         | BSD-3-Clause                                  |                                                                                        |
| ✅     | seroval                                            | 1.5.0         | MIT                                           |                                                                                        |
| ✅     | serve-placeholder                                  | 2.0.2         | MIT                                           |                                                                                        |
| ✅     | serve-static                                       | 2.2.1         | MIT                                           |                                                                                        |
| ✅     | setprototypeof                                     | 1.2.0         | ISC                                           |                                                                                        |
| ✅     | shebang-command                                    | 2.0.0         | MIT                                           |                                                                                        |
| ✅     | shebang-regex                                      | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | shell-quote                                        | 1.8.3         | MIT                                           |                                                                                        |
| ✅     | sigma                                              | 3.0.2         | MIT                                           |                                                                                        |
| ✅     | signal-exit                                        | 4.1.0         | ISC                                           |                                                                                        |
| ✅     | simple-git                                         | 3.30.0        | MIT                                           |                                                                                        |
| ✅     | sirv                                               | 3.0.2         | MIT                                           |                                                                                        |
| ✅     | sisteransi                                         | 1.0.5         | MIT                                           |                                                                                        |
| ✅     | slash                                              | 5.1.0         | MIT                                           |                                                                                        |
| ✅     | smob                                               | 1.5.0         | MIT                                           |                                                                                        |
| ✅     | socket.io-client                                   | 4.8.3         | MIT                                           |                                                                                        |
| ✅     | socket.io-parser                                   | 4.2.5         | MIT                                           |                                                                                        |
| ✅     | source-map                                         | 0.6.1         | BSD-3-Clause                                  |                                                                                        |
| ✅     | source-map-js                                      | 1.2.1         | BSD-3-Clause                                  |                                                                                        |
| ✅     | source-map-support                                 | 0.5.21        | MIT                                           |                                                                                        |
| ✅     | speakingurl                                        | 14.0.1        | BSD                                           |                                                                                        |
| ✅     | srvx                                               | 0.10.1        | MIT                                           |                                                                                        |
| ✅     | standard-as-callback                               | 2.1.0         | MIT                                           |                                                                                        |
| ✅     | statuses                                           | 2.0.2         | MIT                                           |                                                                                        |
| ✅     | std-env                                            | 3.10.0        | MIT                                           |                                                                                        |
| ✅     | streamx                                            | 2.23.0        | MIT                                           |                                                                                        |
| ✅     | string-width                                       | 4.2.3         | MIT                                           |                                                                                        |
| ✅     | string_decoder                                     | 1.1.1         | MIT                                           |                                                                                        |
| ✅     | strip-ansi                                         | 6.0.1         | MIT                                           |                                                                                        |
| ✅     | strip-final-newline                                | 3.0.0         | MIT                                           |                                                                                        |
| ✅     | strip-json-comments                                | 3.1.1         | MIT                                           |                                                                                        |
| ✅     | strip-literal                                      | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | structured-clone-es                                | 1.0.0         | ISC                                           |                                                                                        |
| ✅     | stylehacks                                         | 7.0.7         | MIT                                           |                                                                                        |
| ✅     | superjson                                          | 2.2.6         | MIT                                           |                                                                                        |
| ✅     | supports-color                                     | 7.2.0         | MIT                                           |                                                                                        |
| ✅     | supports-preserve-symlinks-flag                    | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | svgo                                               | 4.0.0         | MIT                                           |                                                                                        |
| ✅     | system-architecture                                | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | tagged-tag                                         | 1.0.0         | MIT                                           |                                                                                        |
| ✅     | tailwind-merge                                     | 3.4.0         | MIT                                           |                                                                                        |
| ✅     | tapable                                            | 2.3.0         | MIT                                           |                                                                                        |
| ✅     | tar                                                | 6.2.1         | ISC                                           |                                                                                        |
| ✅     | tar                                                | 7.5.7         | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | tar-stream                                         | 3.1.7         | MIT                                           |                                                                                        |
| ✅     | terser                                             | 5.46.0        | BSD-2-Clause                                  |                                                                                        |
| ✅     | text-decoder                                       | 1.2.3         | Apache-2.0                                    |                                                                                        |
| ✅     | tiny-invariant                                     | 1.3.3         | MIT                                           |                                                                                        |
| ✅     | tinyexec                                           | 0.3.2         | MIT                                           |                                                                                        |
| ✅     | tinyglobby                                         | 0.2.15        | MIT                                           |                                                                                        |
| ✅     | to-regex-range                                     | 5.0.1         | MIT                                           |                                                                                        |
| ✅     | toidentifier                                       | 1.0.1         | MIT                                           |                                                                                        |
| ✅     | totalist                                           | 3.0.1         | MIT                                           |                                                                                        |
| ✅     | tr46                                               | 0.0.3         | MIT                                           |                                                                                        |
| ✅     | tslib                                              | 2.8.1         | 0BSD                                          |                                                                                        |
| ✅     | type-check                                         | 0.4.0         | MIT                                           |                                                                                        |
| ✅     | type-fest                                          | 5.4.2         | (MIT OR CC0-1.0)                              |                                                                                        |
| ✅     | type-level-regexp                                  | 0.1.17        | MIT                                           |                                                                                        |
| ✅     | typescript                                         | 5.9.3         | Apache-2.0                                    |                                                                                        |
| ✅     | ufo                                                | 1.6.3         | MIT                                           |                                                                                        |
| ✅     | ultrahtml                                          | 1.6.0         | MIT                                           |                                                                                        |
| ✅     | uncrypto                                           | 0.1.3         | MIT                                           |                                                                                        |
| ✅     | unctx                                              | 2.5.0         | MIT                                           |                                                                                        |
| ✅     | undici-types                                       | 6.21.0        | MIT                                           |                                                                                        |
| ✅     | unenv                                              | 2.0.0-rc.24   | MIT                                           |                                                                                        |
| ✅     | unhead                                             | 2.1.2         | MIT                                           |                                                                                        |
| ✅     | unicorn-magic                                      | 0.3.0         | MIT                                           |                                                                                        |
| ✅     | unimport                                           | 4.2.0         | MIT                                           |                                                                                        |
| ✅     | unplugin                                           | 2.3.11        | MIT                                           |                                                                                        |
| ✅     | unplugin-utils                                     | 0.2.5         | MIT                                           |                                                                                        |
| ✅     | unplugin-vue-router                                | 0.19.2        | MIT                                           |                                                                                        |
| ✅     | unstorage                                          | 1.17.4        | MIT                                           |                                                                                        |
| ✅     | untun                                              | 0.1.3         | MIT                                           |                                                                                        |
| ✅     | untyped                                            | 1.5.2         | MIT                                           |                                                                                        |
| ✅     | unwasm                                             | 0.5.3         | MIT                                           |                                                                                        |
| ✅     | update-browserslist-db                             | 1.2.3         | MIT                                           |                                                                                        |
| ✅     | uqr                                                | 0.1.2         | MIT                                           |                                                                                        |
| ✅     | uri-js                                             | 4.4.1         | BSD-2-Clause                                  |                                                                                        |
| ✅     | util-deprecate                                     | 1.0.2         | MIT                                           |                                                                                        |
| ✅     | uuid                                               | 11.1.0        | MIT                                           |                                                                                        |
| ✅     | vite                                               | 7.3.1         | MIT                                           |                                                                                        |
| ✅     | vite-dev-rpc                                       | 1.1.0         | MIT                                           |                                                                                        |
| ✅     | vite-hot-client                                    | 2.1.0         | MIT                                           |                                                                                        |
| ✅     | vite-node                                          | 5.3.0         | MIT                                           |                                                                                        |
| ✅     | vite-plugin-checker                                | 0.12.0        | MIT                                           |                                                                                        |
| ✅     | vite-plugin-inspect                                | 11.3.3        | MIT                                           |                                                                                        |
| ✅     | vite-plugin-vue-tracer                             | 1.2.0         | MIT                                           |                                                                                        |
| ✅     | vscode-uri                                         | 3.1.0         | MIT                                           |                                                                                        |
| ✅     | vue                                                | 3.5.17        | MIT                                           |                                                                                        |
| ✅     | vue-bundle-renderer                                | 2.2.0         | MIT                                           |                                                                                        |
| ✅     | vue-demi                                           | 0.14.10       | MIT                                           |                                                                                        |
| ✅     | vue-devtools-stub                                  | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | vue-router                                         | 4.6.4         | MIT                                           |                                                                                        |
| ✅     | vue3-apexcharts                                    | 1.10.0        | MIT                                           | MIT license per GitHub repo; npm reports Unknown due to missing license field.         |
| ✅     | webidl-conversions                                 | 3.0.1         | BSD-2-Clause                                  |                                                                                        |
| ✅     | webpack-virtual-modules                            | 0.6.2         | MIT                                           |                                                                                        |
| ✅     | whatwg-url                                         | 5.0.0         | MIT                                           |                                                                                        |
| ✅     | which                                              | 2.0.2         | ISC                                           |                                                                                        |
| ✅     | word-wrap                                          | 1.2.5         | MIT                                           |                                                                                        |
| ✅     | wrap-ansi                                          | 7.0.0         | MIT                                           |                                                                                        |
| ✅     | ws                                                 | 8.18.3        | MIT                                           |                                                                                        |
| ✅     | wsl-utils                                          | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | xmlhttprequest-ssl                                 | 2.1.2         | MIT                                           |                                                                                        |
| ✅     | y18n                                               | 5.0.8         | ISC                                           |                                                                                        |
| ✅     | yallist                                            | 3.1.1         | ISC                                           |                                                                                        |
| ✅     | yallist                                            | 5.0.0         | BlueOak-1.0.0                                 |                                                                                        |
| ✅     | yaml                                               | 2.8.2         | ISC                                           |                                                                                        |
| ✅     | yargs                                              | 17.7.2        | MIT                                           |                                                                                        |
| ✅     | yargs-parser                                       | 21.1.1        | ISC                                           |                                                                                        |
| ✅     | yocto-queue                                        | 0.1.0         | MIT                                           |                                                                                        |
| ✅     | youch                                              | 4.1.0-beta.13 | MIT                                           |                                                                                        |
| ✅     | youch-core                                         | 0.3.3         | MIT                                           |                                                                                        |
| ✅     | zip-stream                                         | 6.0.1         | MIT                                           |                                                                                        |

## Docker Images

### External Docker Service Licenses

| Status | Service                         | Image                                                                       | License            | Notes                                                         |
| ------ | ------------------------------- | --------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------- |
| ⚠️     | open-webui                      | `ghcr.io/bbvch-ai/aihub-core/open-webui:v0.6.41`                            | BSD-3-Clause       | Permissive with required branding retention                   |
| ✅     | oauth2-proxy                    | `ghcr.io/bbvch-ai/bbvch-ai/oauth2-proxy:latest`                             | MIT                | Permissive license                                            |
| ✅     | llama.cpp                       | `ghcr.io/bbvch-ai/aihub-core/llama.cpp:server-cuda-b7003`                   | MIT                | Permissive license                                            |
| ✅     | minimal-notebook                | `ghcr.io/bbvch-ai/aihub-core/minimal-notebook:notebook-7.0.6`               | BSD-3-Clause       | Jupyter base image                                            |
| ✅     | clickhouse-server               | `ghcr.io/bbvch-ai/aihub-core/clickhouse/clickhouse-server:25.8`             | Apache-2.0         | Permissive license, used by Langfuse for analytics            |
| ✅     | neo4j                           | `ghcr.io/bbvch-ai/aihub-core/neo4j:5.26.16-community`                       | GPL                | Permissive license                                            |
| ✅     | docker-socket-proxy             | `tecnativa/docker-socket-proxy:0.3`                                         | Apache-2.0         | Permissive license                                            |
| ✅     | pgvector                        | `ghcr.io/bbvch-ai/aihub-core/pgvector:pg17`                                 | PostgreSQL License | BSD-style permissive license                                  |
| ✅     | etcd                            | `ghcr.io/bbvch-ai/aihub-core/etcd:v3.5.25`                                  | Apache-2.0         | Permissive license                                            |
| ✅     | presidio-analyzer               | `ghcr.io/bbvch-ai/aihub-core/presidio-analyzer:2.2.359`                     | MIT                | Permissive license                                            |
| ✅     | nats                            | `ghcr.io/bbvch-ai/aihub-core/nats:2.11.4`                                   | Apache-2.0         | Permissive license                                            |
| ✅     | rclone                          | `ghcr.io/bbvch-ai/aihub-core/rclone:1.71.2`                                 | MIT                | Permissive license                                            |
| ✅     | postgres-documentdb             | `ghcr.io/bbvch-ai/aihub-core/postgres-documentdb:17.0.106.0-ferretdb-2.5.0` | Apache-2.0         | Permissive licenses                                           |
| ✅     | traefik                         | `ghcr.io/bbvch-ai/aihub-core/traefik:v3.6.2`                                | Apache-2.0         | Permissive license                                            |
| ✅     | valkey                          | `ghcr.io/bbvch-ai/aihub-core/valkey:8.0.5`                                  | BSD-3-Clause       | Redis-compatible, standard BSD-3-Clause license               |
| ✅     | postgres                        | `ghcr.io/bbvch-ai/aihub-core/postgres:17`                                   | PostgreSQL License | BSD-style permissive license                                  |
| ✅     | langfuse                        | `ghcr.io/bbvch-ai/aihub-core/langfuse/langfuse:3`                           | MIT                | Open-source LLM observability and evaluation platform         |
| ✅     | dagster                         | `ghcr.io/bbvch-ai/aihub-core/dagster:latest`                                | Apache-2.0         | Permissive license                                            |
| ✅     | litellm                         | `ghcr.io/bbvch-ai/aihub-core/litellm:v1.80.5-stable.1`                      | MIT                | Permissive license                                            |
| ✅     | attu                            | `ghcr.io/bbvch-ai/aihub-core/attu:v2.5.12`                                  | Apache-2.0         | Permissive license                                            |
| ✅     | milvus                          | `ghcr.io/bbvch-ai/aihub-core/milvus:v2.6.7`                                 | Apache-2.0         | Permissive license                                            |
| ✅     | presidio-anonymizer             | `ghcr.io/bbvch-ai/aihub-core/presidio-anonymizer:2.2.359`                   | MIT                | Permissive license                                            |
| ✅     | speaches                        | `ghcr.io/bbvch-ai/aihub-core/speaches:0.8.3-cuda-12.6.3`                    | MIT                | Permissive license                                            |
| ✅     | llama.cpp                       | `ghcr.io/bbvch-ai/aihub-core/llama.cpp:server-b7003`                        | MIT                | Permissive license                                            |
| ✅     | ferretdb                        | `ghcr.io/bbvch-ai/aihub-core/ferretdb:2.5.0`                                | Apache-2.0         | Permissive license                                            |
| ✅     | seaweedfs                       | `ghcr.io/bbvch-ai/aihub-core/seaweedfs:3.97`                                | Apache-2.0         | Permissive license                                            |
| ✅     | speaches                        | `ghcr.io/bbvch-ai/aihub-core/speaches:0.8.3-cpu`                            | MIT                | Permissive license                                            |
| ✅     | pgbouncer                       | `ghcr.io/bbvch-ai/aihub-core/pgbouncer:v1.24.1-p1`                          | ISC                | Based on edoburu/pgbouncer (MIT wrapper); permissive licenses |
| ✅     | aws-cli-alpine                  | `ghcr.io/bbvch-ai/aihub-core/aws-cli-alpine:3.22.1`                         | Apache-2.0         | Permissive license                                            |
| ✅     | dagster                         | `ghcr.io/bbvch-ai/aihub-core/dagster:nightly`                               | Apache-2.0         | Permissive license                                            |
| ✅     | opentelemetry-collector-contrib | `otel/opentelemetry-collector-contrib:latest`                               | Apache-2.0         | Permissive license                                            |
| ✅     | langfuse-worker                 | `ghcr.io/bbvch-ai/aihub-core/langfuse/langfuse-worker:3`                    | MIT                | Langfuse background worker                                    |

### Internal Docker Images (Our Code)

The following are our own services and inherit the license we choose:

- rag_agent (`ghcr.io/bbvch-ai/aihub-core/rag_agent:nightly`)
- mineru-vlm (`ghcr.io/bbvch-ai/aihub-core/mineru-vlm:v2.7.5`)
- namespace_selection_agent (`ghcr.io/bbvch-ai/aihub-core/namespace_selection_agent:latest`)
- web (`ghcr.io/bbvch-ai/aihub-core/web:latest`)
- rag_agent (`ghcr.io/bbvch-ai/aihub-core/rag_agent:latest`)
- retrieval_agent (`ghcr.io/bbvch-ai/aihub-core/retrieval_agent:latest`)
- web (`ghcr.io/bbvch-ai/aihub-core/web:nightly`)
- llm_wrapping_agent (`ghcr.io/bbvch-ai/aihub-core/llm_wrapping_agent:nightly`)
- few_shot_agent (`ghcr.io/bbvch-ai/aihub-core/few_shot_agent:latest`)
- default_rag_pipeline (`ghcr.io/bbvch-ai/aihub-core/default_rag_pipeline:nightly`)
- expert_rag_agent (`ghcr.io/bbvch-ai/aihub-core/expert_rag_agent:nightly`)
- shared_rag_pipeline (`ghcr.io/bbvch-ai/aihub-core/shared_rag_pipeline:latest`)
- shared_rag_pipeline (`ghcr.io/bbvch-ai/aihub-core/shared_rag_pipeline:nightly`)
- llm_wrapping_agent (`ghcr.io/bbvch-ai/aihub-core/llm_wrapping_agent:latest`)
- api (`ghcr.io/bbvch-ai/aihub-core/api:latest`)
- default_rag_pipeline (`ghcr.io/bbvch-ai/aihub-core/default_rag_pipeline:latest`)
- retrieval_agent (`ghcr.io/bbvch-ai/aihub-core/retrieval_agent:nightly`)
- bot (`ghcr.io/bbvch-ai/aihub-core/bot:latest`)
- few_shot_agent (`ghcr.io/bbvch-ai/aihub-core/few_shot_agent:nightly`)
- mineru-api (`ghcr.io/bbvch-ai/aihub-core/mineru-api:v2.7.5`)
- expert_asking_agent (`ghcr.io/bbvch-ai/aihub-core/expert_asking_agent:latest`)
- api (`ghcr.io/bbvch-ai/aihub-core/api:nightly`)
- namespace_selection_agent (`ghcr.io/bbvch-ai/aihub-core/namespace_selection_agent:nightly`)
- expert_rag_agent (`ghcr.io/bbvch-ai/aihub-core/expert_rag_agent:latest`)
- bot (`ghcr.io/bbvch-ai/aihub-core/bot:nightly`)
- expert_asking_agent (`ghcr.io/bbvch-ai/aihub-core/expert_asking_agent:nightly`)
