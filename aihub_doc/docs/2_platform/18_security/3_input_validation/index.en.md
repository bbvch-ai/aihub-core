---
title: Input Validation
index: 3
---

# Input Validation

The Swiss AI-Hub implements comprehensive input validation to protect against common attack vectors including path traversal, MIME type confusion, and malformed data.

## File Upload Validation

### File Type Whitelist

**Implementation**: `aihub_lib/generative_ai/document/types/FileTypeConfig.py`

The platform restricts uploads to approximately 40 approved file extensions across multiple categories: document formats (PDF, Office, text, markdown), image formats (JPEG, PNG, TIFF, WebP), audio formats (WAV, MP3), and structured data (JSON, XML).

### MIME Type Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py`

The `FileUploadRequest` model validates that the provided `content_type` matches the expected MIME type for the file extension. This prevents MIME type confusion attacks where malicious files disguise themselves with incorrect MIME types.

### Filename Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py`

Filenames must start with alphanumeric characters and are validated against:
- **Path traversal prevention**: Blocks `..`, `/`, `\`, null bytes
- **Extension spoofing protection**: Maximum 3 dot-separated parts, 10-character extension limit
- **Pattern enforcement**: `^[a-zA-Z0-9][a-zA-Z0-9 _\-]*(\.[a-zA-Z0-_ \-]+)*\.[a-zA-Z0-9]+$`

### File Size Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py`

The `content_length` field requires files > 0 bytes (empty files rejected). Maximum size limits are enforced at the application or reverse proxy level.

## Namespace and Database Name Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py`

Database and namespace names follow similar validation rules to prevent path traversal in logical storage paths.

## What Input Validation Protects

- ✅ Path traversal attacks
- ✅ MIME type confusion
- ✅ Extension spoofing
- ✅ Null byte injection
- ✅ Executable file uploads
- ✅ Resource exhaustion (via size limits)

## Configuration

Validation rules are hardcoded in the Pydantic models and `FileTypeConfig` class. No environment variables currently control input validation behavior.

**To extend supported file types**: Edit `FileTypeConfig.py`, add extension to `supported_extensions` list, test validation, and assess security implications.

## Related Documentation

- [Malware Prevention](../2_malware_prevention/) - Content scanning for malicious files
- [Authentication & Authorization](../1_authentication/) - User identity and access control
- [Container Security](../4_container_security/) - Isolated file processing
- [RBAC](../../11_access_management/2_permissions/) - Permission-based upload restrictions

## References

- **File Type Config**: `aihub_lib/aihub_lib/generative_ai/document/types/FileTypeConfig.py`
- **Upload Validation**: `aihub_api/aihub_api/routes/file/dto/FileUploadRequest.py`
- **File Service**: `aihub_api/aihub_api/routes/file/FileService.py`
