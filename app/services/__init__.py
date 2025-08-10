"""Service layer for invoice processing.

This package contains the implementation of the core invoice
processing logic used by the API. Breaking the logic into a
service layer makes it easier to test and allows the API layer
to remain thin and focused on HTTP concerns.
"""

__all__ = ["InvoiceProcessor", "ProcessingParams"]
