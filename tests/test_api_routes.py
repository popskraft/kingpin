"""
Тесты FastAPI роутов из packages/server/api/routes.py без внешних зависимостей.
Вызовы делаем напрямую как async-функции.
"""

import pytest
from packages.server.api.routes import root, health


@pytest.mark.asyncio
async def test_root_endpoint_direct_call():
    data = await root()
    assert data["ok"] is True
    assert "service" in data and "socket_io" in data


@pytest.mark.asyncio
async def test_health_endpoint_direct_call():
    data = await health()
    assert data == {"ok": True}
