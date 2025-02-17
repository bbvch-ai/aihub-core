from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler

from fastapi import Request, HTTPException

class MultiAuthHandler(AuthHandler):
    """
    A composite authentication handler that sequentially attempts multiple authentication strategies.

    This handler accepts a variable number of authentication strategies (subclasses of AuthHandler)
    and tries each one in order when handling a request. It collects error details from each strategy
    that fails with a 401 Unauthorized error, and if none of the strategies successfully authenticate the request,
    it raises an HTTPException with a combined error message. If any strategy raises an error other than 401,
    that error is immediately propagated.

    ### How It Works:
    1. Each provided authentication handler is invoked in the order specified.
    2. If a handler successfully authenticates the request by returning an AuthenticatedUser, that user is returned immediately.
    3. If a handler fails with an HTTP 401 error, the error detail is collected and the next handler is tried.
    4. If a handler fails with an error that is not a 401, the exception is raised immediately.
    5. If all handlers fail with 401 errors, a consolidated HTTPException is raised including all the failure messages.

    ### Usage Example:
    ```python
    multi_auth = MultiAuthHandler(
        OAuth2AuthHandler(),
        TokenAuthHandler(),
        NoAuthHandler()  # Optionally include for development
    )

    @app.get("/user/me")
    async def get_user(user: AuthenticatedUser = Depends(multi_auth)):
        return {"name": user.name, "email": user.preferred_username, "roles": user.roles}
    ```

    This design allows you to support multiple authentication strategies in a flexible and modular manner.
    """

    def __init__(self, *handlers: AuthHandler):
        self.handlers = handlers

    async def __call__(self, request: Request) -> AuthenticatedUser:
        """Attempt to authenticate the request using each provided authentication handler in sequence."""
        errors = []
        for handler in self.handlers:
            try:
                user = await handler(request)
                # Return immediately on the first successful authentication.
                return user
            except HTTPException as exc:
                errors.append(f"{handler.__class__.__name__}: {exc.detail}")
                # If the error is not 401, re-raise immediately.
                if exc.status_code != 401:
                    raise exc

        # If no strategy succeeded, raise an error with all failure details.
        raise HTTPException(status_code=401, detail=" | ".join(errors))
