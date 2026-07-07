"""
Guards /admin behind a single admin login (username + password from env
vars). This is intentionally simple: one shared admin account, not a
per-user permissions system. Good enough for "only I can see this table
of clients," which is the actual requirement right now.

Swap this out later for per-admin accounts (tied to the Farmer/Admin
model) if you ever need role-based access like Tupande's "Admin
Permissions" screen.
"""
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"admin_authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin_authenticated"))


def get_admin_auth() -> AdminAuth:
    return AdminAuth(secret_key=settings.SECRET_KEY)
