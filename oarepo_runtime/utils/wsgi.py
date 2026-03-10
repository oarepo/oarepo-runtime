"""WSGI utilities for handling middleware wrappers."""

from flask import current_app


def get_api_app():
    """Get the API app from the WSGI app, traversing middleware wrappers if needed.

    When PROXYFIX_CONFIG is set, the wsgi_app is wrapped in ProxyFix middleware,
    which means we need to traverse the wrapper chain to find the DispatcherMiddleware
    that contains the mounts.

    Returns:
        The API Flask app if found, otherwise falls back to current_app.
    """
    wsgi_app = current_app.wsgi_app
    # Traverse middleware wrappers (e.g., ProxyFix) to find DispatcherMiddleware
    while wsgi_app is not None and not hasattr(wsgi_app, "mounts"):
        wsgi_app = getattr(wsgi_app, "app", None)
    if wsgi_app is not None and "/api" in wsgi_app.mounts:
        return wsgi_app.mounts["/api"]
    return current_app
