# Custom Open Terminal image: pinned upstream sandbox + the two missing file libs.
#
# OpenWebUI routes its code-execution path to this sandbox (the native execute_code
# tool, via TERMINAL_SERVER_CONNECTIONS on the open-webui service). The base image
# already ships Python 3.12 with pandas, openpyxl, xlsxwriter, python-docx,
# python-pptx, weasyprint, pypdf, matplotlib, Pillow, numpy, scipy, lxml and PyYAML,
# plus the ffmpeg and pandoc binaries — only reportlab and fpdf2 are missing, so we
# add just those. That inventory is what the user-facing format matrix in
# docs/docs/2_platform/10_chat_ui/6_coding is verified against: re-verify it there
# when bumping the base tag below, because it decides which file formats the
# sandbox can actually produce.
# Everything installs from binary wheels at build time, so the running container
# needs NO outbound internet (it stays network-isolated on `code-sandbox`).
#
# The full variant (`0.11.34`, not `0.11.34-slim`) is used so OPEN_TERMINAL_MULTI_USER
# works: it ships sudo + useradd and runs as the non-root `user` with passwordless
# sudo, giving per-user home isolation. Its WORKDIR is already the writable /home/user.
#
# Pinned to an explicit version (not `latest`) for reproducible builds — bump this tag
# deliberately. Re-publish via `make -C infra/deployment build-and-push-open-terminal-image`
# after editing this file. Non-build stages then pick it up via `docker compose pull`.
FROM ghcr.io/open-webui/open-terminal:0.11.34

USER root
RUN pip install --no-cache-dir reportlab fpdf2
USER user
