---
title: Programmierung / Softwareentwicklung
source_sha: 820147cd3e9470b283394b49091768f7aa09f69401f0825ab70497b59e3a6831
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

## Generierte Dateien

Während der Code-Ausführung geschriebene Dateien (Reports, Spreadsheets, Diagramme usw.) erscheinen automatisch im
Files-Panel von OpenWebUI, wo Benutzer sie herunterladen können. Nach dem Erstellen einer Datei bestätigt das Modell den
Dateinamen.

Das Erzeugen von Dokumenten ist eine eigenständige Capability und erfordert kein Schreiben von Code. Siehe
[Dateigenerierung](../13_file_generation/) für das empfohlene Modell, die verifizierte Liste der Ausgabeformate und die
dafür geltenden Einschränkungen.

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
