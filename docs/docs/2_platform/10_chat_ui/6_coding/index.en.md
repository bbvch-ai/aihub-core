---
title: Coding / Software Development
---

# Coding / Software Development

OpenWebUI integrates with **Open Terminal** — a sandboxed Linux environment with Python and common document libraries
(pandas, openpyxl, python-docx, reportlab, fpdf2, weasyprint, matplotlib, xlsxwriter). Code runs in an isolated per-user
environment; files created during execution appear in OpenWebUI's Files panel for download.

::: warning
Code execution via Open Terminal is available for **plain LLM models only** (those with native function calling
enabled). AI-Hub agent chats do not currently support code execution — this is a planned follow-up.
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

## Generated files

Files written during code execution (reports, spreadsheets, charts, etc.) automatically appear in OpenWebUI's Files
panel, where users can download them. After creating a file the model will confirm the filename.
