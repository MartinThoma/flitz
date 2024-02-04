"""
MixIns that handle user actions.

Every MixIn should have its own file and be self-contained.
"""

from flitz.actions.deletion import DeletionMixIn
from flitz.actions.show_properties import ShowProperties

__all__ = ["DeletionMixIn", "ShowProperties"]
