"""Blueprints package initialization."""
from flask import Blueprint

# Import all blueprints
from .auth import auth_bp
from .dreams import dreams_bp
from .forum import forum_bp
from .groups import groups_bp

# List of all blueprints to register
all_blueprints = [
    auth_bp,
    dreams_bp,
    forum_bp,
    groups_bp
]
