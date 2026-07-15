"""Secret-encryption interface owned by the domain.

``cryptography`` is a vendor library, so it stays behind this abstraction the
same way ``AIClient`` keeps vendor SDKs out of the domain — the concrete AES-GCM
implementation lives in ``app.infrastructure.crypto``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretCipher(ABC):
    """Contract for encrypting/decrypting small secrets (e.g. API keys) at rest."""

    @abstractmethod
    def encrypt(self, plaintext: str, *, aad: str) -> tuple[str, str]:
        """Encrypt ``plaintext``, bound to ``aad`` (additional authenticated data,
        e.g. the owning user's id). Returns ``(ciphertext_b64, nonce_b64)``."""

    @abstractmethod
    def decrypt(self, ciphertext_b64: str, nonce_b64: str, *, aad: str) -> str:
        """Decrypt a value previously returned by :meth:`encrypt`. Raises if
        ``aad`` does not match what was used at encryption time."""
