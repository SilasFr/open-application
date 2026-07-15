"""AES-256-GCM implementation of the :class:`SecretCipher` interface.

No AWS KMS / cloud key-management service — the master key is a single
env-var-provisioned secret (Constitution: minimal infrastructure surface for an
open-source project with no cloud account beyond Supabase/Render).
"""

from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.domain.crypto import SecretCipher

_NONCE_LENGTH_BYTES = 12


class AesGcmCipher(SecretCipher):
    """Encrypts secrets with AES-256-GCM under a single base64-encoded master key.

    The key is decoded lazily, on first actual use, rather than in ``__init__``:
    this cipher is constructed on every request that might touch a saved BYOK
    key (see ``get_ai_client_resolver``), even though most requests never do
    (no saved key to decrypt). Deferring validation means an unset/blank
    ``master_key_b64`` — the default when an operator hasn't opted into BYOK —
    never breaks ordinary requests; it only fails the rare call that actually
    needs to encrypt or decrypt something, matching this project's "secrets
    default to empty, routes that need them fail loudly only when invoked" rule.
    """

    def __init__(self, *, master_key_b64: str) -> None:
        self._master_key_b64 = master_key_b64

    def _aesgcm(self) -> AESGCM:
        return AESGCM(base64.b64decode(self._master_key_b64))

    def encrypt(self, plaintext: str, *, aad: str) -> tuple[str, str]:
        nonce = os.urandom(_NONCE_LENGTH_BYTES)
        ciphertext = self._aesgcm().encrypt(
            nonce, plaintext.encode("utf-8"), aad.encode("utf-8")
        )
        return (
            base64.b64encode(ciphertext).decode("ascii"),
            base64.b64encode(nonce).decode("ascii"),
        )

    def decrypt(self, ciphertext_b64: str, nonce_b64: str, *, aad: str) -> str:
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        try:
            plaintext = self._aesgcm().decrypt(nonce, ciphertext, aad.encode("utf-8"))
        except InvalidTag as exc:
            raise ValueError("Failed to decrypt secret: wrong key or AAD.") from exc
        return plaintext.decode("utf-8")
