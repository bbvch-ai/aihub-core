"""Backwards-compatible re-export of :func:`test_identity.fake_user`.

Kept as a dedicated module because many call sites import
``from swiss_ai_hub.core.testing.auth_utils.fake_user import fake_user`` directly.
"""

from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

__all__ = ["fake_user"]
