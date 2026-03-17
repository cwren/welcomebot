import logging
from types import SimpleNamespace
import pytest
import pytest
from unittest.mock import AsyncMock, MagicMock

from signalbot import MessageType
from welcomebot import CNCCommand

USER = "user 1"
MANAGER_1 = "user 2"
MANAGER_2 = "user 3"
MANAGERS = [MANAGER_1, MANAGER_2]
CHAT_1 = "thisischat1"
CHAT_2 = "thisischat2"
CHAT_1_NAME = "chat1"
CHAT_2_NAME = "chat2"
GROUPS = [CHAT_1, CHAT_2]
CNC_ID = CHAT_1

logger = logging.getLogger("welcomebot")

@pytest.fixture
def context():
    context = SimpleNamespace()
    context.message = SimpleNamespace()
    context.send = AsyncMock(return_value=3)
    return context

@pytest.fixture
def cnc():
    fake_groups = SimpleNamespace()
    fake_groups.list = MagicMock(return_value=GROUPS)

    fake_bot = SimpleNamespace()
    fake_bot._groups_by_internal_id = {
        CHAT_1: { 'name' : CHAT_1_NAME} ,
        CHAT_2: { 'name' : CHAT_2_NAME} ,
    }
    cnc = CNCCommand(
        logger,
        MANAGERS,
        CNC_ID,
        fake_groups)
    cnc.bot = fake_bot
    return cnc


async def test_hello_1(cnc, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = "Hello"

    await cnc.handle(context)

    assert len(context.send.call_args.args) == 1
    assert "help" in context.send.call_args.args[0]

async def test_hello_2(cnc, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_2
    context.message.text = "Hello"

    await cnc.handle(context)

    assert len(context.send.call_args.args) == 1
    assert "help" in context.send.call_args.args[0]


async def test_reject_dm(cnc, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = None
    context.message.source_uuid = USER
    context.message.text = "Hello"

    await cnc.handle(context)
    assert len(context.send.call_args.args) == 1
    assert "CNC channel" in context.send.call_args.args[0]

async def test_reject_user(cnc, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = USER
    context.message.text = "Hello"

    await cnc.handle(context)
    assert len(context.send.call_args.args) == 1
    assert "from a manager" in context.send.call_args.args[0]

async def test_help(cnc, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = "List"

    await cnc.handle(context)
    assert len(context.send.call_args.args) == 1
    assert CHAT_1_NAME in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]
