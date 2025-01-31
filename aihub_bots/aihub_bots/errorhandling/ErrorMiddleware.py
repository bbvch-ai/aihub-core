import traceback

from botbuilder.core import BotActionNotImplementedError
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class ErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except BotActionNotImplementedError:
            raise HTTPException(status_code=501, detail="Not Implemented")
        except NotImplementedError:
            raise HTTPException(status_code=501, detail="Not Implemented")
        except PermissionError:
            raise HTTPException(status_code=401, detail="Unauthorized")
        except KeyError:
            raise HTTPException(status_code=404, detail="Not Found")
        except HTTPException as http_exc:
            # FastAPI's built-in exception
            return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})
        except Exception:
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
