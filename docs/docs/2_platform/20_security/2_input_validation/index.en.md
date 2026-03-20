---
title: Input Validation
---

# Input Validation

The Swiss AI Hub implements input validation to protect against common attack vectors including path traversal, MIME
type confusion, and malformed data.

## File upload validation

### File type whitelist

The platform restricts uploads to approximately 40 approved file extensions across multiple categories: document formats
(PDF, Office, text, markdown), image formats (JPEG, PNG, TIFF, WebP), audio formats (WAV, MP3), and structured data
(JSON, XML).

### MIME type validation

The platform validates that the provided content type matches the expected MIME type for the file extension. This
prevents MIME type confusion attacks where malicious files disguise themselves with incorrect MIME types.

### Filename validation

Filenames must start with alphanumeric characters and are validated to block:

- Path traversal attempts (`..`, `/`, `\`, null bytes)
- Extension spoofing (maximum 3 dot-separated parts, 10-character extension limit)

### File size validation

Files must be larger than 0 bytes. Empty files are rejected. Maximum size limits are enforced at the application or
reverse proxy level.

## Namespace and database name validation

Database and namespace names follow similar validation rules to prevent path traversal in logical storage paths.

## What input validation protects

- Path traversal attacks
- MIME type confusion
- Extension spoofing
- Null byte injection
- Executable file uploads
- Resource exhaustion (via size limits)

## Related documentation

- [Authentication & Authorization](../1_authentication/) - User identity and access control
- [Container Security](../3_container_security/) - Isolated file processing
- [RBAC](../../11_access_management/2_permissions/) - Permission-based upload restrictions
