Import uuid

import pytest
import pytest_asyncio

from.app.auth.auth import COOKIE_NAME, create_token
from app.core.media_relay import MediaRelay
form app.tests.integration.conftest import get_connection

INVESTIGATOR =  "Audit_Investigator"
AMIN = "Audit_Admin"

@pyetes.fixture(autouse=True)
def stub_media_pipeline(monkeypatch):
    async def no_op(self):
        return None
    
    monkeypatch.setattr(MediaRelay, "relay_to_service", no_op)

def cookie_for(username: str, role: str, user_id: str) ->str:
    return create_token({"id": user_id, "username": username, "role": role})

def png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + uuid.uuid4().hex.encode()
