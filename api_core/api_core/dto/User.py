from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    aud: str                        # Audience: The intended recipient of the token (your application's client ID)
    iss: str                        # Issuer: The authority that issued the token
    iat: datetime                   # Issued At: Timestamp when the token was issued
    nbf: datetime                   # Not Before: Timestamp before which the token is not valid
    exp: datetime                   # Expiration Time: Timestamp when the token expires
    scp: List[str]                  # Scopes: The permissions granted
    sub: str                        # Subject: Identifier for the user
    tid: str                        # Tenant ID: Identifier for your Azure AD tenant
    ver: str                        # Token Version
    name: Optional[str] = None      # User's full name
    preferred_username: EmailStr     # User's preferred username (often their email)
    oid: str                        # Object ID: Unique identifier for the user in Azure AD
    roles: Optional[List[str]] = [] # Roles assigned to the user
    nonce: Optional[str] = None     # Nonce: A value to mitigate replay attacks
    # Add any additional custom claims as needed

    class Config:
        # Allow population by field names and aliases
        allow_population_by_field_name = True
        # Enable parsing of Unix timestamps into datetime objects
        json_encoders = {
            datetime: lambda v: int(v.timestamp())
        }
