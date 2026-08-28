---
title: Coding / Software Development
---

# Coding / Software Development

OpenWebUI integrates with **Open Terminal** — a sandboxed Linux environment with Python 3.12, common document libraries
(pandas, openpyxl, xlsxwriter, python-docx, python-pptx, reportlab, fpdf2, weasyprint, pypdf, matplotlib, Pillow, numpy,
scipy, lxml, PyYAML) and the `ffmpeg` and `pandoc` command-line tools. Code runs in an isolated per-user environment;
files created during execution appear in OpenWebUI's Files panel for download.

::: warning Requirements & current limitations
- **Plain LLM models only.** Code execution is driven by OpenWebUI's native `execute_code` tool, so it works only with
  plain chat models that **support function (tool) calling**, and **Native Function Calling must be enabled** for the
  model (Admin → Settings → Models → the model's advanced params). Models without function-calling support cannot
  trigger the sandbox.
- **AI-Hub agents are not supported yet.** Agent chats own their own generation and do not expose OpenWebUI's
  tool-calling handshake, so code execution does **not** engage for them. This is a planned follow-up.
:::

There are two main ways to use code execution.

1. Ask the model to write and run code. Mentioning a specific goal (e.g. "create a chart", "process this data") gives
   the model the context to generate and execute Python code that produces the result directly in the chat.
2. Provide existing code and ask the model to run or improve it.

## Coding with the LLM

Enter a prompt mentioning the "Pydiode environment" in order to generate code.

![Prompt Pydiode Environment](../../../../media/open_webui/prompt_pydiode_environment.jpeg)

Using the "Run" button the code can be tested directly inside the chat.

![Code with Run Button](../../../../media/open_webui/code_with_run_button.jpeg)

::: tip Two execution paths
**Model-driven execution** — where the model decides to run code to compute an answer or produce a file — runs in the
**Open Terminal** sandbox (server-side, with the document libraries above; generated files appear in the Files panel).
The manual **"Run" button** on a code block uses OpenWebUI's built-in **Pyodide** engine (in-browser WebAssembly), which
is lightweight but limited to its bundled packages and does not write files to the server.
:::

After running the code snippet prints the result below the cell.

![Code Execution Result](../../../../media/open_webui/code_execution_result.jpeg)

## Executing existing code

Select "Code Interpreter".

![Select Code Interpreter](../../../../media/open_webui/select_code_interpreter.jpeg)

Encase the code in back-ticks to mark it as code for execution.

![Code in Backticks](../../../../media/open_webui/code_in_backticks.jpeg)

When the code has run through the result is printed out.

![Code Execution Output](../../../../media/open_webui/code_execution_output.jpeg)

## File generation

Files written during code execution (reports, spreadsheets, charts, etc.) automatically appear in OpenWebUI's Files
panel, where users can download them. After creating a file the model will confirm the filename.

::: tip Recommended model — Workspace → Kimi-K2.6
Select **Kimi-K2.6** in the model picker (under **Workspace**) when you want the model to produce a file.

File generation is a multi-step tool-calling loop: the model has to decide to call `execute_code`, write correct Python,
read the result back and report the filename. Reliability on that loop varies far more between models than the list of
supported formats does. All AI-Hub text-generation models declare function-calling support, but not all of them complete
the handshake in practice — with Open Terminal enabled, `Qwen3.5-122B-A10B-FP8` returns an empty response. See
[ADR: Model Identity as a Platform-Injected System Prompt for Plain LLM Chats](/arc42/decisions/2026_08_14_model_identity_system_prompt_for_plain_llm_chats.md).

**Native Function Calling** still has to be switched on for the chosen model — it is not enabled by default.
:::

### Supported output formats

Verified against the `open-terminal-office:0.11.34` sandbox image. "Can be generated" means the sandbox can write the
file and hand it to the Files panel; it says nothing about whether the same format can be read back in as an upload.

| Category           | File formats                                            | Can be generated | How                                         |
| ------------------ | ------------------------------------------------------- | ---------------- | ------------------------------------------- |
| Text documents     | DOCX, RTF, TXT, Markdown (`.md`), HTML                  | Yes              | `python-docx`, `pandoc`, plain text         |
| Portable documents | PDF                                                     | Yes              | `reportlab`, `fpdf2`, `weasyprint`, `pypdf` |
| Spreadsheets       | XLSX, XLS, CSV                                          | Yes              | `openpyxl`, `xlsxwriter`, `pandas`          |
| Presentations      | PPTX, PDF                                               | Yes              | `python-pptx`, `pandoc`                     |
| Images (raster)    | PNG, JPG/JPEG, TIFF, WebP, BMP                          | Yes              | `Pillow`, `matplotlib`                      |
| Video              | MP4, WebM, MOV, GIF                                     | Yes              | `ffmpeg` (H.264, VP9, GIF)                  |
| Audio              | MP3, WAV, OGG, FLAC                                     | Yes              | `ffmpeg` (LAME, PCM, Vorbis, FLAC)          |
| Source code        | py, cs, java, ts, js, go, rs, cpp, sql, yaml, json, xml | Yes              | Plain text                                  |
| Data exchange      | JSON, XML, YAML, CSV                                    | Yes              | `json`, `lxml`, `PyYAML`, `pandas`          |
| Knowledge bases    | Markdown, HTML, Confluence storage format, MediaWiki    | Yes              | `pandoc`, plain text/XML                    |
| Diagrams (source)  | SVG, Draw.io (`.drawio`), Mermaid, PlantUML             | Source only      | Written as text — see below                 |
| Diagrams (Visio)   | Visio (`.vsdx`)                                         | No               | No library available — see below            |

### Known limitations

::: warning
- **Diagrams are generated as source, not as pictures.** SVG, Draw.io, Mermaid and PlantUML files are text or XML, so
  the sandbox writes them without trouble — but it ships **no renderer** for them (no `cairosvg`, `mmdc`, `plantuml`,
  Graphviz or Inkscape). Ask for a raster image via `matplotlib` instead when you need a picture rather than a source
  file.
- **Visio (`.vsdx`) cannot be generated.** There is no Visio library in the sandbox and no LibreOffice to convert
  through. Ask for `.drawio` or SVG source instead.
- **Reading a format is not the same as writing it.** TIFF and Visio files could not be read back into the sandbox as
  input during capability testing, even though TIFF generation works.
- **The format list is tied to the sandbox image.** It reflects `open-terminal-office:0.11.34`. Bumping that tag can add
  or remove libraries, and therefore formats, without any other visible change.
:::

## Isolation and limitations

::: warning Shared-container, per-user isolation
Open Terminal runs in **a single shared container** with `OPEN_TERMINAL_MULTI_USER` enabled: each user gets a separate
Linux account and home directory (`/home/<user>`), and standard filesystem permissions keep one user's files private
from another. This is **per-user isolation inside one container**, not a container-per-user model — all users share the
same kernel, CPU, memory, `/tmp`, and process list. It suits small, trusted groups; it is **not** a hard multi-tenant
security boundary. Treat the sandbox as a convenience for collaborators, not as a barrier between mutually untrusted
parties.
:::

::: tip Stored files grow over time
Each user's generated files persist on the host (the `open-terminal` `/home` volume) and are **not** cleaned up
automatically — there is currently no retention or quota policy. Disk usage grows with use; operators should monitor the
volume and prune old per-user data manually until an automated cleanup/TTL is added.
:::
