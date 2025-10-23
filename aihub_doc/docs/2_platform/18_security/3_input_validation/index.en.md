---
title: Input Validation
index: 3
---

# Input Validation

The Swiss AI-Hub implements comprehensive input validation to protect against common attack vectors including path traversal, MIME type confusion, and malformed data. These controls are defense-in-depth measures that complement authentication, authorization, and malware prevention.

## File Upload Validation

### File Type Whitelist

**Implementation**: `aihub_lib/generative_ai/document/types/FileTypeConfig.py`

The platform restricts file uploads to approximately 47 approved file extensions across multiple categories:

**Supported Categories**:
- **Document Formats**: PDF, text files, markdown, CSV, HTML, AsciiDoc, Office formats (DOCX, PPTX, XLSX and their variants)
- **Image Formats**: JPEG, PNG, TIFF, BMP, WebP
- **Audio Formats**: WAV, MP3
- **Structured Data**: JSON, XML

**Validation Methods**:
- `is_extension_supported(extension)`: Returns boolean if extension is allowed
- `get_mime_type_for_extension(extension)`: Returns expected MIME type
- `get_unique_extensions()`: Returns complete list of supported extensions

**Security Benefit**: Limits attack surface by rejecting executable files, scripts, and other potentially dangerous file types.

### MIME Type Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py:49-76`

The `FileUploadRequest` model validates MIME type consistency:

1. Extracts file extension from filename
2. Checks extension against whitelist
3. Validates provided `content_type` matches expected MIME type for that extension
4. Rejects uploads where MIME type and extension are inconsistent

**Security Benefit**: Prevents MIME type confusion attacks where malicious files disguise themselves with incorrect MIME types.

### Filename Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py:23-36`

Filenames undergo strict validation:

**Enforced Rules**:
- Must start with alphanumeric character
- Can contain spaces, dashes, underscores in filename body
- Maximum 3 dot-separated parts (prevents excessive extension chains)
- Extension limited to 10 characters
- Blocks path traversal characters: `..`, `/`, `\`, null bytes

**Pattern**: `^[a-zA-Z0-9][a-zA-Z0-9 _\-]*(\.[a-zA-Z0-_ \-]+)*\.[a-zA-Z0-9]+$`

**Security Benefits**:
- ✅ Prevents path traversal attacks
- ✅ Prevents extension spoofing (e.g., `file.pdf.exe.txt`)
- ✅ Blocks null byte injection
- ✅ Enforces predictable, safe naming conventions

### File Size Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py:18`

The `content_length` field requires files to be greater than 0 bytes (empty files rejected). Maximum size limits are enforced at the application or reverse proxy level (Traefik).

**Recommended Limits**:
- Minimum: > 0 bytes (enforced in model)
- Maximum: 100 MB for individual files (configurable)

**Security Benefit**: Prevents resource exhaustion attacks through oversized uploads.

## Namespace and Database Name Validation

**Implementation**: `aihub_api/routes/file/dto/FileUploadRequest.py:39-46`

Database and namespace names used in file paths undergo similar validation:

**Enforced Rules**:
- Must start with alphanumeric character
- Can contain spaces, dashes, underscores
- Blocks path traversal characters: `..`, `/`, `\`, null bytes

**Pattern**: `^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$`

**Security Benefit**: Prevents path traversal in logical storage paths (database/namespace names).

## Input Validation Best Practices

### Defense in Depth

Input validation is one layer in a multi-layered security approach:

1. **Input Validation** (this document) - Reject malformed/malicious input
2. **Authentication & Authorization** ([Authentication](../1_authentication/)) - Verify user identity and permissions
3. **Malware Scanning** ([Malware Prevention](../2_malware_prevention/)) - Detect malicious file content
4. **Encryption** ([Data Encryption](../x_data_encryption/)) - Protect data in transit and at rest

No single control is sufficient - they work together to provide comprehensive protection.

### Whitelist Over Blacklist

The platform uses whitelist-based validation (allowed file types) rather than blacklist-based (blocked file types). This is more secure because:

- ✅ New attack vectors are blocked by default
- ✅ Cannot be bypassed by obscure file extensions
- ✅ Easier to maintain and audit
- ✅ Predictable and explicit behavior

### Fail Secure

All validation failures result in rejected requests with clear error messages. The system never attempts to "fix" invalid input, which could introduce vulnerabilities.

## Limitations

### What Input Validation Does NOT Prevent

**Not Protected Against**:
- ❌ Malware content within valid file types (requires [malware scanning](../2_malware_prevention/))
- ❌ Zero-day exploits in file parsers
- ❌ Malicious content in text files (e.g., SQL injection in CSV)
- ❌ Social engineering attacks

**Protected Against**:
- ✅ Path traversal attacks
- ✅ MIME type confusion
- ✅ Extension spoofing
- ✅ Null byte injection
- ✅ Executable file uploads
- ✅ Resource exhaustion (via size limits)

## Configuration

### Current Configuration

Validation rules are hardcoded in the Pydantic models and `FileTypeConfig` class. No environment variables currently control input validation behavior.

### Extending Supported File Types

To add support for new file extensions:

1. Edit `aihub_lib/generative_ai/document/types/FileTypeConfig.py`
2. Add extension to `supported_extensions` list (with leading dot)
3. Ensure Python's `mimetypes` library recognizes the extension (or add manual mapping)
4. Test validation with sample files
5. Document security considerations for the new file type

**Example**:
```python
# Adding .svg support
supported_extensions: list[str] = [
    # ... existing extensions ...
    ".svg",  # Scalable Vector Graphics
]
```

**Security Consideration**: Always assess whether new file types introduce security risks (e.g., SVG files can contain JavaScript).

## Related Documentation

- [Malware Prevention](../2_malware_prevention/) - Content scanning for malicious files
- [Authentication & Authorization](../1_authentication/) - User identity and access control
- [Container Security](../4_container_security/) - Isolated file processing
- [RBAC](../../11_access_management/2_permissions/) - Permission-based upload restrictions
- [Auditing](../../12_auditing/) - Tracking file upload events

## References

- **File Type Config**: `aihub_lib/aihub_lib/generative_ai/document/types/FileTypeConfig.py`
- **Upload Validation**: `aihub_api/aihub_api/routes/file/dto/FileUploadRequest.py`
- **File Service**: `aihub_api/aihub_api/routes/file/FileService.py`
