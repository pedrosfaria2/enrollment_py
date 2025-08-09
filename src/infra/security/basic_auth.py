import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

_basic_scheme = HTTPBasic(auto_error=False)


class BasicAuthGuard:
    def __init__(self, username: str, password: str, realm: str = "EnrollmentAPI"):
        self.username = username
        self.password = password
        self.realm = realm

    def _unauth(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": f'Basic realm="{self.realm}"'},
        )

    def __call__(
        self,
        credentials: Annotated[HTTPBasicCredentials | None, Depends(_basic_scheme)],
    ) -> str:
        if credentials is None:
            raise self._unauth()
        if not hmac.compare_digest(credentials.username, self.username):
            raise self._unauth()
        if not hmac.compare_digest(credentials.password, self.password):
            raise self._unauth()
        return credentials.username
