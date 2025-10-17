---
title: Supported Identity Providers
index: 6
---

# Supported Identity Providers

The Swiss AI Hub implements standards-based authentication and supports integration with a wide range of enterprise identity providers (IdPs) through OpenID Connect (OIDC) and OAuth 2.0 protocols. This document provides a comprehensive overview of supported identity providers, integration patterns, and configuration guidelines for enterprise deployments.

## Overview

The platform's authentication architecture is built on open standards, ensuring compatibility with any OIDC-compliant identity provider while providing optimized support and documentation for commonly used enterprise identity systems. This approach gives organizations the flexibility to integrate with their existing identity infrastructure without vendor lock-in.

## Primary Supported Identity Providers

### Microsoft Entra ID (Azure Active Directory)

**Support Level**: Fully Supported and Recommended

Microsoft Entra ID (formerly Azure Active Directory) is the primary identity provider for the Swiss AI Hub, with extensive integration and tested compatibility.

**Key Features**:
- **Single Sign-On (SSO)**: Seamless authentication using organizational credentials
- **Multi-Factor Authentication (MFA)**: Leverage existing MFA policies configured in Entra ID
- **Conditional Access**: Support for conditional access policies based on location, device state, and risk level
- **Group-Based Access**: Automatic role assignment based on Entra ID group memberships
- **User Profile Sync**: Retrieve user details (name, email, department) from Microsoft Graph API
- **Application Roles**: Support for Azure AD application roles mapped to platform permissions

**Configuration Requirements**:
```yaml
identity_provider:
  type: "azure_ad"
  tenant_id: "your-tenant-id"
  client_id: "your-application-client-id"
  client_secret: "your-client-secret"  # Use Azure Key Vault in production
  authority: "https://login.microsoftonline.com/{tenant_id}"
  
  # Optional: Advanced configuration
  scopes:
    - "openid"
    - "profile"
    - "email"
    - "User.Read"
  
  graph_api:
    enabled: true
    base_url: "https://graph.microsoft.com/v1.0"
    
  group_sync:
    enabled: true
    role_mapping:
      "Sales Team": "sales_user"
      "HR Administrators": "hr_admin"
      "IT Support": "support_admin"
```

**Azure AD Application Setup**:
1. Register a new application in Azure Portal
2. Configure redirect URIs for your deployment (e.g., `https://your-domain.com/auth/callback`)
3. Generate a client secret
4. Grant API permissions: `User.Read`, `GroupMember.Read.All`
5. Assign users or groups to the application

**Benefits**:
- Native integration with Microsoft 365 ecosystem
- Leverages existing organizational policies
- No additional user credential management
- Comprehensive audit logging in Azure AD

### Generic OpenID Connect (OIDC)

**Support Level**: Fully Supported

Any OIDC-compliant identity provider can be integrated with the Swiss AI Hub using the generic OIDC connector.

**Supported OIDC Providers**:
- Okta
- Auth0
- Keycloak
- Google Workspace (Google Cloud Identity)
- GitLab
- GitHub
- Custom OIDC implementations

**Configuration Requirements**:
```yaml
identity_provider:
  type: "oidc"
  issuer: "https://your-idp.com"  # OIDC discovery endpoint base URL
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  
  # Discovery URL (typically issuer + /.well-known/openid-configuration)
  discovery_url: "https://your-idp.com/.well-known/openid-configuration"
  
  scopes:
    - "openid"
    - "profile"
    - "email"
    
  # Claims mapping
  claims:
    user_id: "sub"          # Unique user identifier
    email: "email"
    name: "name"
    groups: "groups"        # For role assignment
    
  # Optional: Advanced features
  token_validation:
    verify_signature: true
    verify_audience: true
    verify_issuer: true
    leeway_seconds: 30
```

**OIDC Flow**:
1. User initiates login on Swiss AI Hub
2. Redirect to IdP's authorization endpoint
3. User authenticates with IdP
4. IdP redirects back with authorization code
5. Swiss AI Hub exchanges code for ID token and access token
6. User profile is retrieved from UserInfo endpoint
7. User session is established with platform

### OAuth 2.0 Providers

**Support Level**: Supported with Limited Integration

For identity providers that support OAuth 2.0 but not full OIDC, the platform can integrate using OAuth 2.0 flows.

**Common OAuth 2.0 Providers**:
- LinkedIn
- Twitter/X
- Facebook
- Salesforce
- Custom OAuth 2.0 services

**Configuration Requirements**:
```yaml
identity_provider:
  type: "oauth2"
  authorization_endpoint: "https://provider.com/oauth/authorize"
  token_endpoint: "https://provider.com/oauth/token"
  userinfo_endpoint: "https://provider.com/api/user"
  
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  
  scopes:
    - "read:user"
    - "user:email"
    
  # User profile mapping
  profile_mapping:
    user_id: "id"
    email: "email"
    name: "display_name"
```

**Limitations**:
- May require additional API calls for complete user profile
- Limited standardization compared to OIDC
- Potential for provider-specific quirks requiring custom handling

## Enterprise Identity Provider Integrations

### Okta

**Support Level**: Tested and Fully Supported

Okta is a widely-used enterprise identity platform with full OIDC support.

**Configuration Example**:
```yaml
identity_provider:
  type: "oidc"
  issuer: "https://your-domain.okta.com"
  client_id: "your-okta-client-id"
  client_secret: "your-okta-client-secret"
  
  discovery_url: "https://your-domain.okta.com/.well-known/openid-configuration"
  
  scopes:
    - "openid"
    - "profile"
    - "email"
    - "groups"
    
  claims:
    user_id: "sub"
    email: "email"
    name: "name"
    groups: "groups"
```

**Okta-Specific Features**:
- Universal Directory for centralized user management
- Adaptive Multi-Factor Authentication
- API Access Management for token-based API authentication
- User lifecycle management and provisioning

**Setup Instructions**:
1. Create a new "Web" application in Okta Admin Console
2. Set authorization code flow as the grant type
3. Configure redirect URIs
4. Assign users or groups to the application
5. Configure group claims to be included in tokens

### Auth0

**Support Level**: Tested and Fully Supported

Auth0 provides flexible authentication and authorization as a service.

**Configuration Example**:
```yaml
identity_provider:
  type: "oidc"
  issuer: "https://your-tenant.auth0.com"
  client_id: "your-auth0-client-id"
  client_secret: "your-auth0-client-secret"
  
  discovery_url: "https://your-tenant.auth0.com/.well-known/openid-configuration"
  
  scopes:
    - "openid"
    - "profile"
    - "email"
    
  claims:
    user_id: "sub"
    email: "email"
    name: "name"
```

**Auth0-Specific Features**:
- Universal Login for customizable login experience
- Rules and Actions for custom authentication logic
- Social identity provider aggregation
- Passwordless authentication options
- Anomaly detection and breach password detection

**Setup Instructions**:
1. Create a Regular Web Application in Auth0 Dashboard
2. Configure Allowed Callback URLs
3. Enable desired connections (database, social, enterprise)
4. Configure JWT token settings
5. Set up custom claims for role mapping if needed

### Keycloak

**Support Level**: Tested and Fully Supported

Keycloak is an open-source identity and access management solution, ideal for on-premises deployments.

**Configuration Example**:
```yaml
identity_provider:
  type: "oidc"
  issuer: "https://keycloak.your-domain.com/realms/your-realm"
  client_id: "swiss-ai-hub"
  client_secret: "your-client-secret"
  
  discovery_url: "https://keycloak.your-domain.com/realms/your-realm/.well-known/openid-configuration"
  
  scopes:
    - "openid"
    - "profile"
    - "email"
    - "roles"
    
  claims:
    user_id: "sub"
    email: "email"
    name: "name"
    groups: "groups"
    roles: "realm_access.roles"
```

**Keycloak-Specific Features**:
- Self-hosted and open-source
- Multi-realm support for tenant isolation
- User federation (LDAP, Active Directory)
- Fine-grained authorization policies
- Custom authentication flows
- Full control over deployment and data

**Setup Instructions**:
1. Create a new realm in Keycloak admin console
2. Create a new client with "openid-connect" protocol
3. Configure valid redirect URIs
4. Enable "Client authentication" and "Standard flow"
5. Create roles and groups as needed
6. Assign users to roles/groups

### Google Workspace (Google Cloud Identity)

**Support Level**: Tested and Fully Supported

Google Workspace provides OIDC authentication for organizations using Google's productivity suite.

**Configuration Example**:
```yaml
identity_provider:
  type: "oidc"
  issuer: "https://accounts.google.com"
  client_id: "your-google-client-id.apps.googleusercontent.com"
  client_secret: "your-google-client-secret"
  
  discovery_url: "https://accounts.google.com/.well-known/openid-configuration"
  
  scopes:
    - "openid"
    - "email"
    - "profile"
    
  claims:
    user_id: "sub"
    email: "email"
    name: "name"
    
  # Domain restriction (optional)
  hd_parameter: "your-domain.com"  # Restrict to specific Google Workspace domain
```

**Google-Specific Features**:
- Integration with Google Workspace services
- Domain restriction for security
- 2-Step Verification enforcement
- Advanced Protection Program support
- Google Admin console for user management

**Setup Instructions**:
1. Create OAuth 2.0 credentials in Google Cloud Console
2. Configure OAuth consent screen
3. Add authorized redirect URIs
4. Enable Google+ API for user profile access
5. Optionally configure domain restrictions

### LDAP / Active Directory (via Keycloak Federation)

**Support Level**: Supported through Federation

For organizations with existing LDAP or Active Directory infrastructure without OIDC support, Keycloak can provide federation.

**Architecture**:
```
Swiss AI Hub <--> Keycloak (OIDC) <--> LDAP/Active Directory
```

**Setup Approach**:
1. Deploy Keycloak as an OIDC identity provider
2. Configure LDAP/AD user federation in Keycloak
3. Map LDAP attributes to Keycloak user attributes
4. Configure Swiss AI Hub to use Keycloak as OIDC provider
5. Users authenticate through Keycloak, which validates against LDAP/AD

**Benefits**:
- Leverage existing LDAP infrastructure
- Add OIDC capabilities to legacy systems
- Centralized user management remains in AD/LDAP
- No user credential migration required

## Advanced Integration Features

### Group-Based Role Assignment

Automatically assign platform roles based on identity provider group memberships:

```python
async def assign_roles_from_groups(
    user: UserIdentity,
    groups: list[str],
    role_mapping: dict[str, str]
) -> list[str]:
    """Assign roles based on IdP group memberships."""
    assigned_roles = []
    
    for group in groups:
        if group in role_mapping:
            role_name = role_mapping[group]
            await role_service.assign_role(user.id, role_name)
            assigned_roles.append(role_name)
    
    return assigned_roles
```

**Configuration Example**:
```yaml
role_mapping:
  # Azure AD groups
  "Engineering-AI-Team": "data_scientist"
  "Product-Managers": "business_analyst"
  "IT-Administrators": "platform_admin"
  
  # Okta groups  
  "Swiss-AI-Hub-Users": "standard_user"
  "Swiss-AI-Hub-Admins": "platform_admin"
```

### Just-In-Time (JIT) User Provisioning

Automatically create user accounts on first login:

```python
async def jit_provision_user(
    user_claims: dict,
    identity_provider: str
) -> UserIdentity:
    """Provision user on first successful authentication."""
    
    # Extract user information from claims
    user_id = user_claims["sub"]
    email = user_claims["email"]
    name = user_claims.get("name", email)
    
    # Check if user exists
    existing_user = await user_service.get_user_by_external_id(
        user_id, identity_provider
    )
    
    if existing_user:
        # Update profile if changed
        await user_service.update_profile(existing_user.id, user_claims)
        return existing_user
    
    # Create new user
    new_user = await user_service.create_user(
        external_id=user_id,
        identity_provider=identity_provider,
        email=email,
        name=name,
        profile_data=user_claims
    )
    
    # Assign default roles
    await role_service.assign_default_roles(new_user.id)
    
    # Assign roles from groups if available
    if "groups" in user_claims:
        await assign_roles_from_groups(
            new_user, user_claims["groups"], ROLE_MAPPING
        )
    
    return new_user
```

### Single Logout (SLO)

Support for single logout across all connected applications:

**OIDC End Session Endpoint**:
```python
async def logout_user(
    user: UserIdentity,
    idp_end_session_url: str
) -> str:
    """Initiate single logout process."""
    
    # Revoke local session
    await session_service.revoke_session(user.session_id)
    
    # Construct IdP logout URL
    logout_url = (
        f"{idp_end_session_url}"
        f"?id_token_hint={user.id_token}"
        f"&post_logout_redirect_uri=https://your-domain.com/logged-out"
    )
    
    return logout_url
```

### Token Refresh and Lifecycle

Automatic token refresh for long-lived sessions:

```python
async def refresh_access_token(
    user: UserIdentity,
    idp_token_endpoint: str
) -> str:
    """Refresh expired access token using refresh token."""
    
    if not user.refresh_token:
        raise AuthenticationError("No refresh token available")
    
    # Request new access token
    response = await http_client.post(
        idp_token_endpoint,
        data={
            "grant_type": "refresh_token",
            "refresh_token": user.refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )
    
    new_access_token = response.json()["access_token"]
    
    # Update user session
    await session_service.update_access_token(user.id, new_access_token)
    
    return new_access_token
```

## Security Considerations

### Token Validation

All ID tokens are validated for security:

**Validation Checks**:
- **Signature Verification**: Cryptographic validation using IdP's public keys (JWKS)
- **Issuer Validation**: Ensure token was issued by expected IdP
- **Audience Validation**: Verify token is intended for this application
- **Expiration Check**: Reject expired tokens
- **Not Before Check**: Reject tokens used before their valid start time
- **Nonce Validation**: Prevent token replay attacks

**Implementation**:
```python
from jose import jwt, JWTError

async def validate_id_token(
    id_token: str,
    idp_jwks_url: str,
    expected_issuer: str,
    expected_audience: str
) -> dict:
    """Validate ID token according to OIDC specification."""
    
    # Retrieve public keys from IdP
    jwks = await fetch_jwks(idp_jwks_url)
    
    try:
        # Decode and validate token
        claims = jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
            audience=expected_audience,
            issuer=expected_issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True
            }
        )
        
        return claims
        
    except JWTError as e:
        raise AuthenticationError(f"Token validation failed: {e}")
```

### Secure Credential Storage

**Client Secret Management**:
- Never commit secrets to version control
- Use environment variables or secret management services
- Rotate secrets regularly
- Use Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault in production

**Example with Environment Variables**:
```python
import os

CLIENT_SECRET = os.environ.get("IDP_CLIENT_SECRET")
if not CLIENT_SECRET:
    raise ConfigurationError("IDP_CLIENT_SECRET not configured")
```

### PKCE (Proof Key for Code Exchange)

For enhanced security, especially in public clients:

```python
import secrets
import hashlib
import base64

def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge."""
    
    # Generate code verifier (random string)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')
    
    # Generate code challenge (SHA256 hash of verifier)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge
```

## Migration and Testing

### Testing Identity Provider Integration

**Test Checklist**:
- [ ] User can successfully authenticate
- [ ] User profile information is correctly retrieved
- [ ] Group memberships are properly mapped to roles
- [ ] Token refresh works correctly
- [ ] Logout properly terminates session
- [ ] MFA policies are respected
- [ ] Conditional access rules are enforced
- [ ] Error handling provides useful feedback

**Test User Setup**:
Create dedicated test accounts in IdP with various permission levels to verify role mapping and access control.

### Migration from One IdP to Another

**Migration Strategy**:
1. Configure new IdP alongside existing IdP
2. Enable multi-IdP support in platform
3. Migrate test users first
4. Map user identities between IdPs (email as common identifier)
5. Gradually migrate user populations
6. Deprecate old IdP after successful migration

**User Identity Mapping**:
```python
async def migrate_user_identity(
    user: UserIdentity,
    old_idp: str,
    new_idp: str,
    new_external_id: str
):
    """Migrate user from old IdP to new IdP."""
    
    # Add new IdP identity
    await user_service.add_identity_provider(
        user.id,
        identity_provider=new_idp,
        external_id=new_external_id
    )
    
    # Keep old IdP active during transition period
    # Remove after verification
```

## Best Practices

### For Administrators

- **Use Group-Based Role Assignment**: Leverage IdP groups for role management
- **Enable MFA**: Require multi-factor authentication in your IdP
- **Regular Security Audits**: Review IdP integration and access logs
- **Credential Rotation**: Regularly rotate client secrets
- **Monitor Authentication Events**: Set up alerts for failed authentication attempts

### For Developers

- **Follow OIDC Standards**: Implement authentication according to specifications
- **Validate All Tokens**: Never trust tokens without validation
- **Handle Errors Gracefully**: Provide clear error messages without exposing sensitive details
- **Log Security Events**: Log all authentication and authorization events
- **Test Thoroughly**: Test with multiple user scenarios and edge cases

## Conclusion

The Swiss AI Hub's support for multiple identity providers ensures organizations can integrate the platform with their existing identity infrastructure. Through standards-based OIDC and OAuth 2.0 support, combined with tested integrations for popular enterprise identity providers, the platform provides secure, flexible authentication that meets the diverse needs of enterprise deployments. The comprehensive support for features like group-based role assignment, JIT provisioning, and single logout ensures seamless integration with organizational identity management practices.
