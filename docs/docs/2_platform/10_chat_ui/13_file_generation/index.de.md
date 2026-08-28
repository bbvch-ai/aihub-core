---
title: Dateigenerierung
source_sha: 04685dcb4afe8126fff35b4f1dbfd763a3664235062a1b6c0e3f936f79bac0f4
---

# Dateigenerierung

Bitten Sie ein Modell, eine Datei zu erzeugen — einen Report, ein Spreadsheet, ein Diagramm, eine Präsentation — und es
schreibt diese Datei mit Python innerhalb der **Open Terminal**-Sandbox. Anschließend öffnet es die fertige Datei in
Ihrem File-Viewer und bestätigt den Dateinamen; die Datei bleibt zudem über den File-Browser des Terminal-Panels
erreichbar.

Sie müssen dafür weder Code schreiben noch lesen. Beschreiben Sie das gewünschte Dokument und lassen Sie es vom Modell
erzeugen.

::: warning Voraussetzungen
Die Dateigenerierung läuft über denselben Pfad wie [Programmierung / Softwareentwicklung](../6_coding/) und erbt daher
dessen Einschränkungen: ein **einfaches LLM-Modell** (kein AI-Hub Agent — diese werden noch nicht unterstützt), mit
dafür **aktiviertem Native Function Calling** (Admin → Settings → Models → die Advanced Params des Modells), und ein im
Chat **ausgewähltes Terminal**. Ohne Native Function Calling kann das Modell die mehrstufige Schleife nicht ausführen,
die der Aufbau einer Datei erfordert. Auf jener Seite finden Sie die Mechanik der Sandbox, das Isolationsmodell pro
Benutzer und den Hinweis, dass generierte Dateien unbegrenzt aufbewahrt werden.
:::

::: tip Empfohlenes Modell — Workspace → Kimi-K2.6
Wählen Sie **Kimi-K2.6** im Modell-Picker (unter **Workspace**), wenn das Modell eine Datei erzeugen soll.

Die Dateigenerierung ist eine mehrstufige Tool-Calling-Schleife: Das Modell muss korrektes Python schreiben, es mit
`run_command` ausführen, das Ergebnis zurücklesen und die Datei dann mit `display_file` übergeben. Die Zuverlässigkeit
dieser Schleife variiert zwischen den Modellen deutlich stärker als die Liste der unterstützten Formate. Alle AI-Hub
Text-Generation-Modelle deklarieren Function-Calling-Unterstützung, aber nicht alle vollziehen den Handshake in der
Praxis — bei aktiviertem Open Terminal liefert `Qwen3.5-122B-A10B-FP8` eine leere Antwort. Siehe
[ADR: Model Identity as a Platform-Injected System Prompt for Plain LLM Chats](/arc42/decisions/2026_08_14_model_identity_system_prompt_for_plain_llm_chats.md).

**Native Function Calling** muss für das gewählte Modell dennoch aktiviert werden — es ist nicht standardmäßig aktiv.
:::

## Unterstützte Ausgabeformate

Was Sie anfragen können. Verifiziert gegen das Sandbox-Image `open-terminal-office:0.11.34` — „Ja" bedeutet, Sie
erhalten eine echte, funktionierende Datei; „Nur Source" bedeutet, Sie erhalten den Textquellcode des Diagramms statt
eines Bildes; „Nein" bedeutet, es ist nicht möglich. Dies sagt nichts darüber aus, ob dasselbe Format als Upload wieder
eingelesen werden kann.

| Kategorie          | Dateiformate                                            | Kann generiert werden |
| ------------------ | ------------------------------------------------------- | --------------------- |
| Textdokumente      | DOCX, RTF, TXT, Markdown (`.md`), HTML                  | Ja                    |
| Portable Dokumente | PDF                                                     | Ja                    |
| Spreadsheets       | XLSX, XLS, CSV                                          | Ja                    |
| Präsentationen     | PPTX, PDF                                               | Ja                    |
| Bilder (Raster)    | PNG, JPG/JPEG, TIFF, WebP, BMP                          | Ja                    |
| Video              | MP4, WebM, MOV, GIF                                     | Ja                    |
| Audio              | MP3, WAV, OGG, FLAC                                     | Ja                    |
| Quellcode          | py, cs, java, ts, js, go, rs, cpp, sql, yaml, json, xml | Ja                    |
| Datenaustausch     | JSON, XML, YAML, CSV                                    | Ja                    |
| Knowledge Bases    | Markdown, HTML, Confluence Storage Format, MediaWiki    | Ja                    |
| Diagramme (Source) | SVG, Draw.io (`.drawio`), Mermaid, PlantUML             | Nur Source            |
| Diagramme (Visio)  | Visio (`.vsdx`)                                         | Nein                  |

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
