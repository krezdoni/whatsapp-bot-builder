"""Test field-level encryption — core security invariant."""
import os
import pytest
from cryptography.fernet import Fernet

# Set up test env before importing anything from src
os.environ["FIELD_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-tests-only"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"

from src.health_profile.encryption import (
    encrypt_field, decrypt_field, encrypt_json, decrypt_json
)


def test_encrypt_decrypt_roundtrip():
    user_id = "user-abc-123"
    plaintext = "Hypertension, Type 2 Diabetes"
    token = encrypt_field(plaintext, user_id)
    assert token != plaintext
    assert decrypt_field(token, user_id) == plaintext


def test_different_users_get_different_ciphertext():
    text = "same health data"
    token_a = encrypt_field(text, "user-a")
    token_b = encrypt_field(text, "user-b")
    assert token_a != token_b


def test_user_b_cannot_decrypt_user_a_data():
    token_a = encrypt_field("sensitive data", "user-a")
    with pytest.raises(Exception):
        decrypt_field(token_a, "user-b")


def test_encrypt_decrypt_json():
    user_id = "user-json-test"
    data = [{"name": "Metformin", "dose": "500mg", "active": True}]
    token = encrypt_json(data, user_id)
    result = decrypt_json(token, user_id)
    assert result == data


def test_json_nested_structures():
    user_id = "user-nested"
    data = {"conditions": ["T2DM", "HTN"], "labs": {"HbA1c": 6.8, "unit": "%"}}
    assert decrypt_json(encrypt_json(data, user_id), user_id) == data
