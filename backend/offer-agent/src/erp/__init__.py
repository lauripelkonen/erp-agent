"""
ERP Abstraction Layer

Provides a unified interface for working with multiple ERP systems.
Use the ERPFactory to instantiate the correct ERP adapter based on configuration.
"""

from src.erp.factory import ERPFactory, get_erp_factory

__all__ = [
    "ERPFactory",
    "get_erp_factory",
]
