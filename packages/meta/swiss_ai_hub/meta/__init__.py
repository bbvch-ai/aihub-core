"""Marker module for the ``swiss-ai-hub`` meta-package.

This distribution ships no functionality of its own — it exists to claim the bare
``swiss-ai-hub`` name and to install the full Swiss AI Hub SDK in one step. Import the
real modules from the packages this distribution depends on (``swiss_ai_hub.core``,
``swiss_ai_hub.agent``, …).
"""

from importlib.metadata import version

__version__ = version("swiss-ai-hub")
