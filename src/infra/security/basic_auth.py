import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

_basic_scheme = HTTPBasic(auto_error=False)


class BasicAuthGuard:
    """HTTP Basic Authentication guard for FastAPI endpoints.
    
    Provides secure username/password authentication using constant-time comparison
    to prevent timing attacks.
    """
    
    def __init__(self, username: str, password: str, realm: str = "EnrollmentAPI"):
        """Initialize authentication guard with credentials.
        
        Args:
            username: Expected username for authentication
            password: Expected password for authentication
            realm: HTTP Basic Auth realm name (default: "EnrollmentAPI")
        """
        self.username = username
        self.password = password
        self.realm = realm

    def _unauth(self) -> HTTPException:
        """Create HTTP 401 Unauthorized exception.
        
        Returns:
            HTTPException with 401 status and WWW-Authenticate header
        """
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
        )

    def __call__(
        self,
        credentials: Annotated[HTTPBasicCredentials | None, Depends(_basic_scheme)],
    ) -> str:
        """Authenticate HTTP Basic credentials.
        
        Validates username and password using constant-time comparison
        to prevent timing attacks.
        
        Args:
            credentials: HTTP Basic credentials from request
            
        Returns:
            Authenticated username
            
        Raises:
            HTTPException: If credentials are missing or invalid
        """
        if credentials is None:
            raise self._unauth()
        if not hmac.compare_digest(credentials.username, self.username):
            raise self._unauth()
        if not hmac.compare_digest(credentials.password, self.password):
            raise self._unauth()
        return credentials.username
