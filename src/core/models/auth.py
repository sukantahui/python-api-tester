"""
PyRestForge - Authentication Domain Models (Pydantic v2)
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AuthType(str, Enum):
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    DIGEST = "digest"
    INHERIT = "inherit"


class ApiKeyLocation(str, Enum):
    HEADER = "header"
    QUERY = "query"


class OAuth2GrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"


class AuthConfig(BaseModel):
    """Unified Authentication configuration model."""
    type: AuthType = Field(default=AuthType.NONE, description="Active authentication type")
    
    # Bearer Token fields
    bearer_token: Optional[str] = Field(default=None, description="Bearer token string or template {{token}}")
    bearer_prefix: Optional[str] = Field(default="Bearer", description="Prefix prepended before token")
    
    # Basic Auth fields
    basic_username: Optional[str] = Field(default=None, description="Basic Auth Username")
    basic_password: Optional[str] = Field(default=None, description="Basic Auth Password")
    
    # API Key fields
    api_key_name: Optional[str] = Field(default=None, description="API Key parameter or header name (e.g. X-Api-Key)")
    api_key_value: Optional[str] = Field(default=None, description="API Key value or template")
    api_key_location: ApiKeyLocation = Field(default=ApiKeyLocation.HEADER, description="Placement in Header or Query")
    
    # OAuth 2.0 fields
    oauth2_grant_type: OAuth2GrantType = Field(default=OAuth2GrantType.CLIENT_CREDENTIALS)
    oauth2_access_token_url: Optional[str] = Field(default=None)
    oauth2_client_id: Optional[str] = Field(default=None)
    oauth2_client_secret: Optional[str] = Field(default=None)
    oauth2_scope: Optional[str] = Field(default=None)
    oauth2_access_token: Optional[str] = Field(default=None)
    
    # Digest Auth fields
    digest_username: Optional[str] = Field(default=None)
    digest_password: Optional[str] = Field(default=None)
    digest_realm: Optional[str] = Field(default=None)
    digest_nonce: Optional[str] = Field(default=None)
