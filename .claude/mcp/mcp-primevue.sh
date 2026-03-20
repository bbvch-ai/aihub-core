#!/bin/bash
set -e
# PrimeVue MCP — official MCP server for the PrimeVue component library.
# Provides AI assistants with comprehensive access to PrimeVue component documentation
# including props, events, slots, methods, theming (Pass Through), and design tokens.
#
# The swiss_ai_hub_web frontend uses PrimeVue 4.x as its primary UI component library.
# This gives much richer context than generic documentation lookups.
cd "$(dirname "$0")/../.."
exec npx -y @primevue/mcp
