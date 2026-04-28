import uuid
from flask import request, g

def init_audit_context(app):
    @app.before_request
    def before_request():
        # Correlation ID
        g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # User & Org (filled by JWT or decorators)
        g.user_id = None
        g.org_id = None
        
    @app.after_request
    def after_request(response):
        response.headers["X-Correlation-ID"] = getattr(g, "correlation_id", "")
        return response
