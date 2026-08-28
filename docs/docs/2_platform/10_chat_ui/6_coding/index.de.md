---
title: Programmierung / Softwareentwicklung
source_sha: fed56eac7b0aec32c6b93eb4e57ce6b808c2c2cb2689ef97487591d21100d0b8
---

# Programmierung / Softwareentwicklung

OpenWebUI integriert **Open Terminal** — eine gesandboxte Linux-Umgebung mit Python 3.12, gängigen Dokumenten-Libraries
(pandas, openpyxl, xlsxwriter, python-docx, python-pptx, reportlab, fpdf2, weasyprint, pypdf, matplotlib, Pillow, numpy,
scipy, lxml, PyYAML) sowie den Command-Line Tools `ffmpeg` und `pandoc`. Der Code läuft in einer isolierten Umgebung pro
Benutzer; während der Ausführung erstellte Dateien erscheinen im Files-Panel von OpenWebUI zum Download.

::: warning Voraussetzungen & aktuelle Einschränkungen
- **Nur einfache LLM-Modelle.** Die Code-Ausführung wird durch das native `execute_code`-Tool von OpenWebUI gesteuert
  und funktioniert daher nur mit einfachen Chat-Modellen, die **Function (Tool) Calling unterstützen**, und **Native
  Function Calling muss** für das Modell **aktiviert sein** (Admin → Settings → Models → die Advanced Params des
  Modells). Modelle ohne Function-Calling-Unterstützung können die Sandbox nicht auslösen.
- **AI-Hub Agents werden noch nicht unterstützt.** Agent-Chats steuern ihre eigene Generierung und stellen den
  Tool-Calling-Handshake von OpenWebUI nicht bereit, weshalb die Code-Ausführung für sie **nicht** aktiv wird. Dies ist
  ein geplanter Follow-up.
:::

Es gibt zwei Hauptwege, die Code-Ausführung zu nutzen.

1. Bitten Sie das Modell, Code zu schreiben und auszuführen. Die Nennung eines konkreten Ziels (z. B. „ein Diagramm
   erstellen", „diese Daten verarbeiten") gibt dem Modell den Kontext, um Python-Code zu generieren und auszuführen, der
   das Ergebnis direkt im Chat erzeugt.
2. Stellen Sie bestehenden Code bereit und bitten Sie das Modell, ihn auszuführen oder zu verbessern.

## Programmierung mit dem LLM

Geben Sie einen Prompt ein, der die „Pydiode environment" erwähnt, um Code zu generieren.

![Prompt Pydiode Environment](../../../../media/open_webui/prompt_pydiode_environment.jpeg)

Mit dem „Run"-Button kann der Code direkt im Chat getestet werden.

![Code with Run Button](../../../../media/open_webui/code_with_run_button.jpeg)

::: tip Zwei Ausführungspfade
**Modellgesteuerte Ausführung** — bei der das Modell entscheidet, Code auszuführen, um eine Antwort zu berechnen oder
eine Datei zu erzeugen — läuft in der **Open Terminal**-Sandbox (serverseitig, mit den oben genannten
Dokumenten-Libraries; generierte Dateien erscheinen im Files-Panel). Der manuelle **„Run"-Button** an einem Code-Block
nutzt die eingebaute **Pyodide**-Engine von OpenWebUI (In-Browser-WebAssembly), die leichtgewichtig ist, aber auf ihre
mitgelieferten Packages beschränkt bleibt und keine Dateien auf dem Server schreibt.
:::

Nach der Ausführung gibt das Code-Snippet das Ergebnis unterhalb der Zelle aus.

![Code Execution Result](../../../../media/open_webui/code_execution_result.jpeg)

## Ausführen von bestehendem Code

Wählen Sie „Code Interpreter".

![Select Code Interpreter](../../../../media/open_webui/select_code_interpreter.jpeg)

Fassen Sie den Code in Backticks ein, um ihn als auszuführenden Code zu kennzeichnen.

![Code in Backticks](../../../../media/open_webui/code_in_backticks.jpeg)

Wenn der Code ausgeführt wurde, wird das Ergebnis ausgegeben.

![Code Execution Output](../../../../media/open_webui/code_execution_output.jpeg)

## Dateigenerierung

Während der Code-Ausführung geschriebene Dateien (Reports, Spreadsheets, Diagramme usw.) erscheinen automatisch im
Files-Panel von OpenWebUI, wo Benutzer sie herunterladen können. Nach dem Erstellen einer Datei bestätigt das Modell den
Dateinamen.

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

### Unterstützte Ausgabeformate

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

### Bekannte Einschränkungen

::: warning
- **Diagramme werden als Source generiert, nicht als Bild.** SVG-, Draw.io-, Mermaid- und PlantUML-Dateien sind Text
  oder XML, die Sandbox schreibt sie also problemlos — sie liefert dafür jedoch **keinen Renderer** mit (kein
  `cairosvg`, `mmdc`, `plantuml`, Graphviz oder Inkscape). Fragen Sie stattdessen ein Rasterbild über `matplotlib` an,
  wenn Sie ein Bild und keine Source-Datei benötigen.
- **Visio (`.vsdx`) kann nicht generiert werden.** Es gibt keine Visio-Library in der Sandbox und kein LibreOffice zum
  Konvertieren. Fragen Sie stattdessen `.drawio`- oder SVG-Source an.
- **Ein Format lesen ist nicht dasselbe wie es schreiben.** TIFF- und Visio-Dateien konnten während der Verifikation der
  Capability nicht als Input in die Sandbox eingelesen werden, obwohl die TIFF-Generierung funktioniert.
- **Die Formatliste ist an das Sandbox-Image gebunden.** Sie bezieht sich auf `open-terminal-office:0.11.34`. Ein
  Anheben dieses Tags kann Libraries und damit Formate hinzufügen oder entfernen, ohne jede andere sichtbare Änderung.
:::

## Isolation und Einschränkungen

::: warning Geteilter Container, Isolation pro Benutzer
Open Terminal läuft in **einem einzigen geteilten Container** mit aktiviertem `OPEN_TERMINAL_MULTI_USER`: Jeder Benutzer
erhält einen separaten Linux-Account und ein eigenes Home-Verzeichnis (`/home/<user>`), und die
Standard-Dateisystemberechtigungen halten die Dateien eines Benutzers vor anderen privat. Dies ist **Isolation pro
Benutzer innerhalb eines Containers**, kein Container-pro-Benutzer-Modell — alle Benutzer teilen denselben Kernel, CPU,
Memory, `/tmp` und die Prozessliste. Es eignet sich für kleine, vertrauenswürdige Gruppen; es ist **keine** harte
Multi-Tenant-Sicherheitsgrenze. Betrachten Sie die Sandbox als Komfort für Mitarbeitende, nicht als Barriere zwischen
sich gegenseitig nicht vertrauenden Parteien.
:::

::: tip Gespeicherte Dateien wachsen über die Zeit
Die generierten Dateien jedes Benutzers persistieren auf dem Host (das `/home`-Volume von `open-terminal`) und werden
**nicht** automatisch aufgeräumt — es gibt derzeit keine Retention- oder Quota-Policy. Der Speicherbedarf wächst mit der
Nutzung; Betreiber sollten das Volume überwachen und alte Benutzerdaten manuell entfernen, bis ein automatisches
Cleanup/TTL hinzugefügt wird.
:::
