---
title: Dateigenerierung
source_sha: 73caf73bb3fd24736a4b68c9ec8375a9392a2b1c06a5608a3491e0e045d51ff3
---

# Dateigenerierung

Bitten Sie ein Modell, eine Datei zu erzeugen — einen Report, ein Spreadsheet, ein Diagramm, eine Präsentation — und es
schreibt diese Datei mit Python innerhalb der **Open Terminal**-Sandbox. Die fertige Datei erscheint im Files-Panel von
OpenWebUI, wo sie heruntergeladen werden kann; nach dem Erstellen bestätigt das Modell den Dateinamen.

Sie müssen dafür weder Code schreiben noch lesen. Beschreiben Sie das gewünschte Dokument und lassen Sie es vom Modell
erzeugen.

::: warning Voraussetzungen
Die Dateigenerierung läuft über denselben Code-Ausführungspfad wie [Programmierung / Softwareentwicklung](../6_coding/)
und erbt daher dessen Einschränkungen: Sie funktioniert nur mit **einfachen LLM-Modellen, die Function (Tool) Calling
unterstützen**, **Native Function Calling muss** für das Modell **aktiviert sein** (Admin → Settings → Models → die
Advanced Params des Modells), und **AI-Hub Agents werden noch nicht unterstützt**. Auf jener Seite finden Sie die
Mechanik der Sandbox, das Isolationsmodell pro Benutzer und den Hinweis, dass generierte Dateien unbegrenzt aufbewahrt
werden.
:::

::: tip Empfohlenes Modell — Workspace → Kimi-K2.6
Wählen Sie **Kimi-K2.6** im Modell-Picker (unter **Workspace**), wenn das Modell eine Datei erzeugen soll.

Die Dateigenerierung ist eine mehrstufige Tool-Calling-Schleife: Das Modell muss entscheiden, `execute_code` aufzurufen,
korrektes Python schreiben, das Ergebnis zurücklesen und den Dateinamen melden. Die Zuverlässigkeit dieser Schleife
variiert zwischen den Modellen deutlich stärker als die Liste der unterstützten Formate. Alle AI-Hub
Text-Generation-Modelle deklarieren Function-Calling-Unterstützung, aber nicht alle vollziehen den Handshake in der
Praxis — bei aktiviertem Open Terminal liefert `Qwen3.5-122B-A10B-FP8` eine leere Antwort. Siehe
[ADR: Model Identity as a Platform-Injected System Prompt for Plain LLM Chats](/arc42/decisions/2026_08_14_model_identity_system_prompt_for_plain_llm_chats.md).

**Native Function Calling** muss für das gewählte Modell dennoch aktiviert werden — es ist nicht standardmäßig aktiv.
:::

## Unterstützte Ausgabeformate

Verifiziert gegen das Sandbox-Image `open-terminal-office:0.11.34`. „Kann generiert werden" bedeutet, dass die Sandbox
die Datei schreiben und an das Files-Panel übergeben kann; es sagt nichts darüber aus, ob dasselbe Format als Upload
wieder eingelesen werden kann.

| Kategorie          | Dateiformate                                            | Kann generiert werden | Wie                                         |
| ------------------ | ------------------------------------------------------- | --------------------- | ------------------------------------------- |
| Textdokumente      | DOCX, RTF, TXT, Markdown (`.md`), HTML                  | Ja                    | `python-docx`, `pandoc`, Plain Text         |
| Portable Dokumente | PDF                                                     | Ja                    | `reportlab`, `fpdf2`, `weasyprint`, `pypdf` |
| Spreadsheets       | XLSX, XLS, CSV                                          | Ja                    | `openpyxl`, `xlsxwriter`, `pandas`          |
| Präsentationen     | PPTX, PDF                                               | Ja                    | `python-pptx`, `pandoc`                     |
| Bilder (Raster)    | PNG, JPG/JPEG, TIFF, WebP, BMP                          | Ja                    | `Pillow`, `matplotlib`                      |
| Video              | MP4, WebM, MOV, GIF                                     | Ja                    | `ffmpeg` (H.264, VP9, GIF)                  |
| Audio              | MP3, WAV, OGG, FLAC                                     | Ja                    | `ffmpeg` (LAME, PCM, Vorbis, FLAC)          |
| Quellcode          | py, cs, java, ts, js, go, rs, cpp, sql, yaml, json, xml | Ja                    | Plain Text                                  |
| Datenaustausch     | JSON, XML, YAML, CSV                                    | Ja                    | `json`, `lxml`, `PyYAML`, `pandas`          |
| Knowledge Bases    | Markdown, HTML, Confluence Storage Format, MediaWiki    | Ja                    | `pandoc`, Plain Text/XML                    |
| Diagramme (Source) | SVG, Draw.io (`.drawio`), Mermaid, PlantUML             | Nur Source            | Wird als Text geschrieben — siehe unten     |
| Diagramme (Visio)  | Visio (`.vsdx`)                                         | Nein                  | Keine Library verfügbar — siehe unten       |

## Bekannte Einschränkungen

::: warning
- **Diagramme werden als Source generiert, nicht als Bild.** SVG-, Draw.io-, Mermaid- und PlantUML-Dateien sind Text
  oder XML, die Sandbox schreibt sie also problemlos — sie liefert dafür jedoch **keinen Renderer** mit (kein
  `cairosvg`, `mmdc`, `plantuml`, Graphviz oder Inkscape) und kann sie daher nicht in eine Bilddatei umwandeln. Fragen
  Sie stattdessen ein Rasterbild über `matplotlib` an, wenn Sie ein Bild und keine Source-Datei benötigen. Beachten Sie,
  dass Mermaid *in einer Chat-Antwort* ein separater Pfad ist: Die Chat-Oberfläche rendert dieses inline als Diagramm —
  deshalb kann eine Mermaid-Antwort gerendert aussehen, während eine Mermaid-**Datei** Source bleibt.
- **Visio (`.vsdx`) kann nicht generiert werden.** Es gibt keine Visio-Library in der Sandbox und kein LibreOffice zum
  Konvertieren. Fragen Sie stattdessen `.drawio`- oder SVG-Source an.
- **Ein Format lesen ist nicht dasselbe wie es schreiben.** TIFF- und Visio-Dateien konnten während der Verifikation der
  Capability nicht als Input in die Sandbox eingelesen werden, obwohl die TIFF-Generierung funktioniert.
- **Die Formatliste ist an das Sandbox-Image gebunden.** Sie bezieht sich auf `open-terminal-office:0.11.34`. Ein
  Anheben dieses Tags kann Libraries und damit Formate hinzufügen oder entfernen, ohne jede andere sichtbare Änderung.
:::
