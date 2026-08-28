---
title: File generation
---

# File generation

Ask a model to produce a file — a report, a spreadsheet, a chart, a slide deck — and it writes that file inside the
**Open Terminal** sandbox using Python. The finished file appears in OpenWebUI's Files panel, where it can be
downloaded; after creating it the model confirms the filename.

You do not need to write or read any code to use this. Describe the document you want and let the model produce it.

::: warning Requirements
File generation runs on the same code-execution path as [Coding / Software Development](../6_coding/), so it inherits
that path's constraints: it works only with **plain LLM models that support function (tool) calling**, **Native Function
Calling must be enabled** for the model (Admin → Settings → Models → the model's advanced params), and **AI-Hub agents
are not supported yet**. See that page for the sandbox mechanics, the per-user isolation model, and the fact that
generated files are kept indefinitely.
:::

::: tip Recommended model — Workspace → Kimi-K2.6
Select **Kimi-K2.6** in the model picker (under **Workspace**) when you want the model to produce a file.

File generation is a multi-step tool-calling loop: the model has to decide to call `execute_code`, write correct Python,
read the result back and report the filename. Reliability on that loop varies far more between models than the list of
supported formats does. All AI-Hub text-generation models declare function-calling support, but not all of them complete
the handshake in practice — with Open Terminal enabled, `Qwen3.5-122B-A10B-FP8` returns an empty response. See
[ADR: Model Identity as a Platform-Injected System Prompt for Plain LLM Chats](/arc42/decisions/2026_08_14_model_identity_system_prompt_for_plain_llm_chats.md).

**Native Function Calling** still has to be switched on for the chosen model — it is not enabled by default.
:::

## Supported output formats

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

## Known limitations

::: warning
- **Diagrams are generated as source, not as pictures.** SVG, Draw.io, Mermaid and PlantUML files are text or XML, so
  the sandbox writes them without trouble — but it ships **no renderer** for them (no `cairosvg`, `mmdc`, `plantuml`,
  Graphviz or Inkscape), so it cannot turn them into an image file. Ask for a raster image via `matplotlib` instead when
  you need a picture rather than a source file. Note that Mermaid returned *in a chat response* is a separate path: the
  chat UI renders that inline as a diagram, which is why a Mermaid answer can look rendered while a Mermaid **file**
  stays source.
- **Visio (`.vsdx`) cannot be generated.** There is no Visio library in the sandbox and no LibreOffice to convert
  through. Ask for `.drawio` or SVG source instead.
- **Reading a format is not the same as writing it.** TIFF and Visio files could not be read back into the sandbox as
  input during capability testing, even though TIFF generation works.
- **The format list is tied to the sandbox image.** It reflects `open-terminal-office:0.11.34`. Bumping that tag can add
  or remove libraries, and therefore formats, without any other visible change.
:::
