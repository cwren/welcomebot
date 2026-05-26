from datetime import datetime, UTC
from unittest.mock import MagicMock
from types import SimpleNamespace

from welcomebot import to_ymd, today

async def test_real_today():
    assert today() > 2461000 # safely in the past

DATE = [ 2026, 5, 26, 16, 47, 10, 1, UTC ]
TODAY = 2461186

async def test_fake_today():
    now = datetime(*DATE)
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=now)
    assert today(dt) == TODAY

async def test_decode():
    assert to_ymd(TODAY) == '2026-05-25'
    assert to_ymd(TODAY - 1) == '2026-05-24'
