"""
Main FastAPI application for the PDF invoice reader.

This module creates the FastAPI app and includes the routers
for the meta (health/version) endpoints and the invoice processing
endpoint. The implementation here is intentionally minimal to
demonstrate a working scaffold that can be expanded upon.
"""

from fastapi import FastAPI

from .controllers.meta_controller import router as meta_router
from .controllers.invoice_controller import router as invoice_router



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="PDF Invoice Reader")
    app.include_router(meta_router)
    app.include_router(invoice_router)
    return app


app = create_app()
