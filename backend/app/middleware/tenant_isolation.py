from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextvars import ContextVar, Token
from uuid import UUID
from typing import Optional

tenant_id_context: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # In a real scenario, we might extract tenant_id from header or user token
        # For now, we rely on the auth dependency to set this context if needed,
        # or we inspect the request state.
        # But commonly, middleware runs before auth.
        # If the tenant ID is in the header 'X-Tenant-ID':
        token: Optional[Token] = None
        tenant_header = request.headers.get("X-Tenant-ID")

        if tenant_header:
            try:
                # Validate UUID
                tid = UUID(tenant_header)
                token = tenant_id_context.set(tid)
            except ValueError:
                pass  # Invalid UUID format, ignore

        try:
            response = await call_next(request)
            return response
        finally:
            # Reset context if it was set
            if token is not None:
                tenant_id_context.reset(token)

def get_current_tenant_id() -> UUID | None:
    return tenant_id_context.get()
