#!/bin/bash
set -e
# Playwright MCP — browser automation and UI debugging for the Nuxt 3 admin interface.
# Enables visual inspection, screenshot capture, DOM/CSS analysis, JavaScript execution,
# and automated UI interaction in a real browser (Chromium, headless by default).
#
# Official Microsoft Playwright MCP server. Browser binaries are auto-installed on first use.
# Use for: debugging frontend issues, verifying UI changes, running visual checks,
# inspecting network requests, and testing OpenWebUI/Admin UI interactions.
cd "$(dirname "$0")/../.."
exec npx -y @playwright/mcp@latest --headless
