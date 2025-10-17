---
title: Source Attribution Security
index: 4
---

# Source Attribution Security

The Swiss AI Hub implements comprehensive security measures for source attribution and external references to ensure that information retrieved from knowledge bases and external sources is safe, trustworthy, and compliant with enterprise security policies. This document describes how the platform protects against malicious content, validates external references, and maintains the integrity of source citations.

## Overview

Source attribution is a critical feature that enables users to trace AI-generated responses back to their original sources. However, exposing source references introduces potential security risks:

- **Cross-Site Scripting (XSS)**: Malicious scripts embedded in document metadata or URLs
- **Phishing Attacks**: Fraudulent URLs disguised as legitimate sources
- **Information Disclosure**: Exposure of internal file paths or sensitive system information
- **Content Injection**: Manipulation of source citations to mislead users
- **Open Redirect Vulnerabilities**: URLs that redirect through untrusted intermediaries

The Swiss AI Hub addresses these risks through multiple layers of protection.

## Source Reference Validation

### URL Sanitization and Validation

All URLs referenced in source attributions undergo strict validation before being presented to users:

**Protocol Whitelisting**: Only safe protocols are permitted:
- `https://` - Secure web resources (preferred)
- `http://` - Non-secure web resources (with warning indication)
- `file://` - Internal file references (restricted to authorized users and sanitized paths)

Blocked protocols include:
- `javascript:` - Script execution vectors
- `data:` - Inline data URIs that can contain executable code
- `vbscript:` - Legacy script execution
- Any custom protocols not explicitly whitelisted

**URL Structure Validation**: Each URL is parsed and validated:
```python
from urllib.parse import urlparse

def validate_source_url(url: str) -> bool:
    """Validate source URL for safety."""
    parsed = urlparse(url)
    
    # Check protocol
    if parsed.scheme not in ['https', 'http', 'file']:
        return False
    
    # Validate domain (for http/https)
    if parsed.scheme in ['https', 'http']:
        if not is_trusted_domain(parsed.netloc):
            return False
    
    # Check for suspicious patterns
    if any(pattern in url.lower() for pattern in BLOCKED_PATTERNS):
        return False
    
    return True
```

**Domain Validation**: For web URLs, domains are validated against:
- **Trusted Domain Whitelist**: Explicitly approved external domains
- **Internal Domain List**: Organization's known internal domains
- **Blocklist**: Known malicious or suspicious domains

### Content Security Policy (CSP) for Source Links

When source links are rendered in the user interface, strict Content Security Policy headers ensure:

**Link Target Isolation**: External links open in new tabs with security attributes:
```html
<a href="https://trusted-source.com/doc.pdf" 
   target="_blank" 
   rel="noopener noreferrer nofollow">
    Document Source
</a>
```

**Security Attributes**:
- `target="_blank"`: Opens in new tab to prevent tab-nabbing
- `rel="noopener"`: Prevents new page from accessing window.opener
- `rel="noreferrer"`: Strips referrer information for privacy
- `rel="nofollow"`: Signals search engines not to follow (SEO protection)

### File Path Sanitization

Internal file references undergo additional sanitization:

**Path Traversal Prevention**: Block directory traversal attempts:
- Strip `../` sequences
- Block absolute paths outside allowed directories
- Normalize paths to canonical form

**Sensitive Path Filtering**: Redact or block references to:
- System directories (`/etc`, `/sys`, `/proc`)
- User home directories
- Application configuration directories
- Temporary directories containing potentially sensitive data

**Example Sanitization**:
```python
def sanitize_file_path(path: str) -> str:
    """Sanitize file paths for safe display."""
    # Normalize the path
    normalized = os.path.normpath(path)
    
    # Check if path tries to escape allowed directories
    if not normalized.startswith(ALLOWED_BASE_PATHS):
        raise ValueError("Path outside allowed directories")
    
    # Remove sensitive path components
    for sensitive in SENSITIVE_PATH_COMPONENTS:
        if sensitive in normalized:
            raise ValueError("Path contains sensitive component")
    
    return normalized
```

## Document Metadata Security

### Metadata Sanitization During Ingestion

When documents are ingested into knowledge bases, metadata is sanitized to prevent security issues:

**HTML and Script Stripping**: Remove all HTML tags and scripts from metadata fields:
- Document titles
- Author names
- Descriptions
- Custom metadata fields

**Character Encoding Validation**: Ensure all metadata uses safe character encodings:
- Reject or sanitize control characters
- Normalize Unicode to prevent homograph attacks
- Validate UTF-8 encoding

**Size Limits**: Enforce maximum sizes for metadata fields to prevent:
- Denial of service through extremely large metadata
- Buffer overflow vulnerabilities
- UI rendering issues

### XSS Prevention in Source Citations

Source citations displayed in the UI are protected against XSS attacks:

**Output Encoding**: All user-generated content is HTML-encoded:
```python
from html import escape

def render_source_citation(title: str, author: str, url: str) -> str:
    """Safely render a source citation."""
    return f"""
        <div class="source-citation">
            <span class="title">{escape(title)}</span>
            <span class="author">{escape(author)}</span>
            <a href="{escape(url)}" target="_blank" rel="noopener noreferrer">
                View Source
            </a>
        </div>
    """
```

**Template Injection Prevention**: Use parameterized templates rather than string concatenation

**Framework Protection**: Leverage framework-level XSS protection (e.g., React's automatic escaping)

## External Resource Security

### Configurable External Access Policies

Organizations can configure policies for accessing external resources:

**Domain Whitelisting**: Define approved external domains:
```yaml
external_sources:
  allowed_domains:
    - "*.company.com"
    - "docs.microsoft.com"
    - "aws.amazon.com"
  blocked_domains:
    - "*.suspicious-domain.com"
```

**Access Control by User Role**: Different users have different external access permissions:
- **Standard Users**: Can only view sources from internal domains
- **Power Users**: Can access pre-approved external domains
- **Administrators**: Can access any validated external source

**Network-Level Restrictions**: For air-gapped or highly secure deployments:
- Block all external URL references
- Display only internal file system sources
- Require administrator approval for adding external sources

### Secure External Content Fetching

When the platform needs to fetch external content (e.g., for web search results):

**Proxy Through Security Gateway**: All external requests route through a security proxy:
- URL validation and sanitization
- Malware scanning of fetched content
- Rate limiting to prevent abuse
- Logging for audit trails

**Timeout and Size Limits**: Prevent resource exhaustion:
```python
async def fetch_external_content(url: str) -> bytes:
    """Safely fetch external content."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0),  # 10 second timeout
        limits=httpx.Limits(max_connections=10)
    ) as client:
        response = await client.get(
            url,
            follow_redirects=False,  # Prevent open redirects
            headers={"User-Agent": "Swiss-AI-Hub/1.0"}
        )
        
        # Enforce size limit
        if response.headers.get("content-length"):
            size = int(response.headers["content-length"])
            if size > MAX_CONTENT_SIZE:
                raise ValueError("Content too large")
        
        return response.content[:MAX_CONTENT_SIZE]
```

**SSL/TLS Verification**: Always verify SSL certificates for HTTPS requests:
- Reject self-signed certificates (unless explicitly trusted)
- Validate certificate chains
- Check certificate revocation status

## Knowledge Base Access Control

### Permission-Based Source Visibility

Source references respect the same RBAC permissions as the underlying knowledge:

**Access Control Integration**: Users can only see source references for documents they have permission to access:

```python
async def get_source_references(
    user: UserIdentity,
    access_checker: AccessChecker,
    query_results: list[SearchResult]
) -> list[SourceReference]:
    """Get source references the user has permission to view."""
    visible_sources = []
    
    for result in query_results:
        # Check if user has access to the knowledge base
        has_access = await access_checker.check_access(
            user,
            f"aihub.user.knowledge.{result.knowledge_base}"
        )
        
        if has_access:
            visible_sources.append(result.source_reference)
    
    return visible_sources
```

**Redacted Source References**: For partial access scenarios:
- Show that sources exist but hide identifying information
- Display source count without revealing specifics
- Provide access request mechanisms for restricted sources

### Data Leakage Prevention

**Snippet Length Limits**: Source excerpts shown in citations are limited to prevent:
- Excessive data exposure in responses
- Reconstruction of full documents from snippets
- Exposure of sensitive context around retrieved information

**Sensitive Data Detection**: Automatic detection and redaction of:
- Credit card numbers
- Social security numbers
- API keys and tokens
- Email addresses (configurable)
- Phone numbers (configurable)

**Watermarking** (optional): For highly sensitive documents:
- Embed invisible user identifiers in displayed snippets
- Track which user accessed which sources
- Enable forensic analysis in case of data leaks

## Web Search Integration Security

### Secure Web Search Results

When integrating web search capabilities:

**Result Filtering**: Web search results are filtered for:
- Malicious or compromised websites
- Low-trust domains
- Known phishing sites
- Adult or inappropriate content (based on organizational policy)

**Link Validation**: All search result links undergo the same validation as other external sources

**Safe Browsing API Integration**: Check URLs against Google Safe Browsing or similar services:
```python
async def validate_search_result(url: str) -> bool:
    """Validate search result URL against threat databases."""
    # Check against Google Safe Browsing API
    threat_status = await safe_browsing_api.check_url(url)
    
    if threat_status in ["MALWARE", "PHISHING", "SOCIAL_ENGINEERING"]:
        return False
    
    # Check against internal blocklist
    if is_blocked_domain(url):
        return False
    
    return True
```

### User Warnings for External Content

**Visual Indicators**: The UI clearly indicates when content is from external sources:
- External link icons
- Color-coded source badges (internal vs. external)
- Hover tooltips showing full URLs
- Security warnings for non-HTTPS sources

**Confirmation Dialogs**: For high-security deployments, require user confirmation:
```
⚠️ External Link Warning

You are about to visit an external website:
https://example.com/document.pdf

This link leads outside your organization. Proceed with caution.

[Cancel] [Continue]
```

## Document Upload Security

### Upload Validation

Documents uploaded to knowledge bases undergo security validation:

**File Type Validation**: Only allow approved file types:
- PDF documents
- Microsoft Office formats (docx, xlsx, pptx)
- Plain text and markdown
- Common image formats (for OCR processing)

**Content Scanning**: Scan uploaded files for:
- Malware and viruses using antivirus engines
- Embedded scripts in PDFs and Office documents
- Macros and executable content
- Suspicious file signatures

**Size Limits**: Enforce maximum file sizes to prevent:
- Resource exhaustion
- Denial of service attacks
- Storage overflow

### Metadata Extraction Security

**Sandboxed Processing**: Extract metadata in isolated environments:
- Prevent malicious documents from exploiting extraction tools
- Limit resource usage during processing
- Contain failures to prevent service disruption

**Metadata Validation**: Validate extracted metadata before storage:
- Check for malicious URLs in document properties
- Sanitize author names and titles
- Remove embedded scripts or macros from metadata fields

## Compliance and Audit

### Source Access Logging

All source reference access is logged for audit purposes:

```json
{
  "event_type": "source_reference_accessed",
  "user_id": "user@example.com",
  "user_oid": "user-oid-456",
  "knowledge_base": "company_policies",
  "document_id": "policy_doc_123",
  "source_url": "file:///policies/vacation_policy.pdf",
  "access_method": "rag_retrieval",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

**Audit Reports**: Generate reports showing:
- Which users accessed which sources
- Frequency of external source access
- Blocked or suspicious source access attempts
- Compliance with source access policies

### Regulatory Compliance

**GDPR Compliance**: Source references respect data protection requirements:
- Right to access: Users can request logs of their source access
- Right to erasure: Source references can be deleted as part of user data deletion
- Data minimization: Only necessary source information is retained

**Data Classification**: Sources can be tagged with sensitivity levels:
- Public: Freely accessible sources
- Internal: Organization-internal documents
- Confidential: Restricted access sources
- Secret: Highly restricted sources requiring special authorization

## Best Practices

### For Administrators

- **Whitelist Trusted Domains**: Maintain an up-to-date list of approved external domains
- **Regular Security Reviews**: Periodically audit source access patterns for anomalies
- **User Training**: Educate users about safe external link practices
- **Incident Response**: Define procedures for responding to suspicious source access

### For Content Managers

- **Validate Sources**: Review document metadata before uploading to knowledge bases
- **Use HTTPS**: Prefer HTTPS URLs for external references
- **Internal First**: Prioritize internal sources over external sources when both are available
- **Regular Audits**: Review and update source references to ensure they remain valid and safe

### For Developers

- **Always Sanitize**: Never trust user-provided URLs or document metadata
- **Defense in Depth**: Implement multiple layers of validation and sanitization
- **Fail Securely**: When validation fails, deny access rather than attempting to fix
- **Log Security Events**: Record all source validation failures for security monitoring

## Conclusion

The Swiss AI Hub's comprehensive source attribution security ensures that references to external content and knowledge sources are safe, validated, and compliant with enterprise security policies. Through multiple layers of validation, sanitization, and access control, the platform protects users from malicious content while maintaining the transparency and traceability that makes source attribution valuable. These security measures enable organizations to confidently deploy AI systems that leverage both internal knowledge and external resources without compromising security or compliance.
