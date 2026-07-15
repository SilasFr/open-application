"""Unit tests for AesGcmCipher: round-trip and AAD-mismatch behavior."""

from __future__ import annotations

import base64

import pytest

from app.infrastructure.crypto.aes_gcm_cipher import AesGcmCipher

_MASTER_KEY_B64 = base64.b64encode(b"0" * 32).decode("ascii")


def _cipher() -> AesGcmCipher:
    return AesGcmCipher(master_key_b64=_MASTER_KEY_B64)


def test_encrypt_then_decrypt_round_trips() -> None:
    cipher = _cipher()
    ciphertext, nonce = cipher.encrypt("sk-super-secret-key", aad="user-1")

    plaintext = cipher.decrypt(ciphertext, nonce, aad="user-1")

    assert plaintext == "sk-super-secret-key"


def test_ciphertext_does_not_contain_plaintext() -> None:
    cipher = _cipher()
    ciphertext, _ = cipher.encrypt("sk-super-secret-key", aad="user-1")

    assert "sk-super-secret-key" not in ciphertext


def test_decrypt_fails_under_wrong_aad() -> None:
    cipher = _cipher()
    ciphertext, nonce = cipher.encrypt("sk-super-secret-key", aad="user-1")

    with pytest.raises(ValueError):
        cipher.decrypt(ciphertext, nonce, aad="user-2")


def test_decrypt_fails_under_wrong_key() -> None:
    cipher = _cipher()
    ciphertext, nonce = cipher.encrypt("sk-super-secret-key", aad="user-1")

    other_key = base64.b64encode(b"1" * 32).decode("ascii")
    other_cipher = AesGcmCipher(master_key_b64=other_key)

    with pytest.raises(ValueError):
        other_cipher.decrypt(ciphertext, nonce, aad="user-1")
