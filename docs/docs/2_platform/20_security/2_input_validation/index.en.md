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

### Files sent inline to agents

API callers can send files to an agent as base64 inside the request. These are checked separately before anything is
stored:

- A JSON request body larger than `API_REQUEST_MAX_JSON_BODY_BYTES` (64 MB) is refused with `413` while it arrives,
  before it is parsed.
- Each file is limited to `AGENT_INLINE_FILE_MAX_FILE_BYTES` (25 MB), and a request to
  `AGENT_INLINE_FILE_MAX_FILES_PER_REQUEST` (10) files.
- The filename may not contain path separators, the content must be valid base64, and the type must be one the agents'
  document readers support. Images are refused, since they belong in the message itself.
- Images inside a message are limited to `AGENT_INLINE_IMAGE_MAX_BYTES` (5 MB) and must be PNG, JPEG, GIF or WebP, so no
  stored image can carry script the way an SVG can. A message may not name a file path for an image, nor reference an
  image stored for another agent: stored images are named by the digest of their content, so only someone who holds an
  image can reference it.
- All files and images of a request are checked before the first is stored, so a refused request leaves nothing behind.

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
