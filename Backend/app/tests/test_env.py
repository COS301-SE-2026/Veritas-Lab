import pytest

from app.core.env import ENVLoader

def test_get_required(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")

    env = ENVLoader()
    result = env.getRequiredEnv("DATABASE_URL")

    assert result == "postgresql://test"

def test_get_required_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    env = ENVLoader()

    with pytest.raises(RuntimeError) as error:
        env.getRequiredEnv("DATABASE_URL")

    assert "Missing required environment variable: DATABASE_URL" in str(error.value)

def test_get_required_env_empty(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")

    env = ENVLoader()

    with pytest.raises(RuntimeError) as error:
        env.getRequiredEnv("DATABASE_URL")

    assert "Missing required environment variable: DATABASE_URL" in str(error.value)

def test_get_required_env_spaces(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "   ")

    env = ENVLoader()

    with pytest.raises(RuntimeError) as error:
        env.getRequiredEnv("DATABASE_URL")

    assert "Missing required environment variable: DATABASE_URL" in str(error.value)

def test_get_optional_set(monkeypatch):
    monkeypatch.setenv("HASH", "HS256")

    env = ENVLoader()
    result = env.getOptionalEnv("HASH", "HS256")

    assert result == "HS256"

def test_get_optional_env_missing(monkeypatch):
    monkeypatch.delenv("HASH", raising=False)

    env = ENVLoader()
    result = env.getOptionalEnv("HASH", "HS256")

    assert result == "HS256"

def test_get_optional_env_empty(monkeypatch):
    monkeypatch.setenv("HASH", "")

    env = ENVLoader()
    result = env.getOptionalEnv("HASH", "HS256")

    assert result == "HS256"

def test_get_required_int(monkeypatch):
    monkeypatch.setenv("TOKEN_EXPIRE", "10")

    env = ENVLoader()
    result = env.getRequiredIntEnv("TOKEN_EXPIRE")

    assert result == 10
    assert isinstance(result, int)

def test_get_required_int_missing(monkeypatch):
    monkeypatch.delenv("TOKEN_EXPIRE", raising=False)

    env = ENVLoader()

    with pytest.raises(RuntimeError) as error:
        env.getRequiredIntEnv("TOKEN_EXPIRE")

    assert "Missing required environment variable: TOKEN_EXPIRE" in str(error.value)

def test_get_required_int_not_int(monkeypatch):
    monkeypatch.setenv("TOKEN_EXPIRE", "abc")

    env = ENVLoader()

    with pytest.raises(RuntimeError) as error:
        env.getRequiredIntEnv("TOKEN_EXPIRE")

    assert "TOKEN_EXPIRE must be a valid integer" in str(error.value)