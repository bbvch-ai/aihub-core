#!/bin/bash
set -e
# SonarQube MCP — official MCP server by SonarSource (io.github.SonarSource/sonarqube-mcp-server).
# Reads the SonarCloud analysis for this repo directly: issues, quality gate, measures, and the
# rule descriptions behind a finding — so review feedback can be pulled instead of relayed by hand.
#
# CI analyses each package as its own SonarCloud project under the `bbv-ai` organization
# (see packages/*/sonar-project.properties, e.g. aihub-core_lib-core), scanned by
# .github/actions/sonarcloud_scan.
#
# SETUP: add SONARQUBE_TOKEN to your .env file.
# Signing in to SonarCloud with GitHub SSO is fine — a user token is separate from how you log in.
# Generate one at https://sonarcloud.io/account/security (My Account -> Security -> Generate Token),
# type "User Token". No SonarCloud admin rights are needed to read your own projects.
#
# The image publishes only a :latest tag, so it is pinned by digest to keep every developer on the
# same server build. Update deliberately with:
#   docker buildx imagetools inspect mcp/sonarqube:latest
SONARQUBE_MCP_IMAGE="mcp/sonarqube@sha256:925c88bc7cab2a1e1025b0bd43f0af504cd8ce1b99e9663ececaca914fb632e7"

cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

if [[ -z "$SONARQUBE_TOKEN" ]]; then
  echo "SonarQube MCP requires SONARQUBE_TOKEN in .env" >&2
  echo "Generate a User Token at: https://sonarcloud.io/account/security" >&2
  echo "GitHub SSO login still lets you mint one — it is independent of the sign-in method." >&2
  exit 1
fi

# SONARQUBE_ORG selects SonarQube Cloud; SONARQUBE_URL would instead target a self-hosted server.
exec docker run -i --rm \
  -e "SONARQUBE_TOKEN=$SONARQUBE_TOKEN" \
  -e "SONARQUBE_ORG=${SONARQUBE_ORG:-bbv-ai}" \
  "$SONARQUBE_MCP_IMAGE"
