---
title: Programmierung / Softwareentwicklung
source_sha: 7d2350bab17cc800c6d66787e8f18d9c8eb4eacc587f787c84730f4c68ee9d92
---

# Programmierung / Softwareentwicklung

Wenn es darum geht, mit Hilfe eines Modells zu programmieren, gibt es zwei Hauptwege, dies zu tun.

1. Entweder schreibt das Modell den Code, was durch die Erwähnung der "Pydiode environment", die zur Ausführung des
   Codes verwendet wird, angedeutet werden kann. Dies gibt dem Modell den Hinweis, dass der Benutzer mit Code arbeiten
   möchte und wird versuchen, die Anfrage durch das Schreiben von Code zu beantworten.
2. Alternativ kann der Chat auch verwendet werden, um bestehenden Code auszuführen und weiterzuentwickeln.

## Programmierung mit dem LLM

Geben Sie einen Prompt ein, der die "Pydiode environment" erwähnt, um Code zu generieren.

![Prompt Pydiode Environment](../../../../media/open_webui/prompt_pydiode_environment.jpeg)

Mit dem "Run"-Button kann der Code direkt im Chat getestet werden.

![Code with Run Button](../../../../media/open_webui/code_with_run_button.jpeg)

Nach der Ausführung gibt das Code-Snippet das Ergebnis unterhalb der Zelle aus.

![Code Execution Result](../../../../media/open_webui/code_execution_result.jpeg)

## Ausführen von bestehendem Code

Wählen Sie "Code Interpreter".

![Select Code Interpreter](../../../../media/open_webui/select_code_interpreter.jpeg)

Fassen Sie den Code in Backticks ein, um ihn als auszuführenden Code zu kennzeichnen.

![Code in Backticks](../../../../media/open_webui/code_in_backticks.jpeg)

Wenn der Code ausgeführt wurde, wird das Ergebnis ausgegeben.

![Code Execution Output](../../../../media/open_webui/code_execution_output.jpeg)
