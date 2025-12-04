# controllers/__init__.py
"""
Controllers package
Chứa các controller xử lý logic nghiệp vụ
"""

from .auth_controller import auth_bp
from .admin_controller import admin_bp, admin_required
from .user_controller import user_bp
from .route_controller import route_bp
from .trip_controller import trip_bp

__all__ = ['auth_bp', 'admin_bp', 'admin_required', 'user_bp', 'route_bp', 'trip_bp']