"""Shared constants for Keycloak realm roles used across the auth module."""

SYS_ADMIN_ROLE = "AIHubSysAdmin"

# What a sysadmin may do through OpenWebUI's signed headers: chat with whatever the acting tenant offers. The headers
# only prove who the user is, so they never carry the sysadmin bypass (tenant deletion, every tenant's data).
SYS_ADMIN_OPENWEBUI_ACCESS_RULES = ["aihub.user.>"]
