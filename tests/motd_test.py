import logging
from types import SimpleNamespace
import pytest
import pytest
from unittest.mock import AsyncMock, MagicMock

from signalbot import MessageType
from welcomebot import MotDCommand

USER_1 = "user1"
USER_2 = "user2"
CNC_CHAT = "cncchatID"
SOCIAL_CHAT = "socialchatID"
NEW_CHAT = "newchatID"
CNC_CHAT_NAME = "cncchat"
SOCIAL_CHAT_NAME = "socialchat"
GROUPS = [CNC_CHAT, SOCIAL_CHAT]
SOCIAL_CHAT_MEMBERS = [ USER_1 ]

logger = logging.getLogger("welcomebot")

@pytest.fixture
def context():
    context = SimpleNamespace()
    context.message = SimpleNamespace()
    context.send = AsyncMock(return_value=3)
    return context

@pytest.fixture
def motd():
    fake_groups = SimpleNamespace()
    fake_groups.list = MagicMock(return_value=GROUPS)
    fake_groups.get_members = MagicMock(return_value=SOCIAL_CHAT_MEMBERS)
    fake_groups.put_members = MagicMock()
    fake_groups.retain_only = MagicMock()

    fake_bot = SimpleNamespace()
    fake_bot._groups_by_internal_id = {
        CNC_CHAT: { 
            'name' : CNC_CHAT_NAME,
            'members' : [ USER_1 ]
        },
        SOCIAL_CHAT: {
            'name' : SOCIAL_CHAT_NAME,
            'members' : SOCIAL_CHAT_MEMBERS,
        },
    }
    motd = MotDCommand(
        logger,
        CNC_CHAT,
        fake_groups)
    motd.bot = fake_bot
    return motd


async def test_hello(motd, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = SOCIAL_CHAT
    context.message.source_uuid = USER_1
    context.message.text = "Hello"

    await motd.handle(context)

    assert len(context.send.call_args.args) == 1
    assert "Hello" in context.send.call_args.args[0]


async def test_reject_dm(motd, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = None
    context.message.source_uuid = USER_1
    context.message.text = "Hello"

    await motd.handle(context)

    assert len(context.send.call_args.args) == 1
    assert "group chats" in context.send.call_args.args[0]


async def test_ignore_cnc_data(motd, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_CHAT
    context.message.source_uuid = USER_1
    context.message.text = "Hello"

    await motd.handle(context)

    assert not context.send.called


async def test_ignore_cnc_update(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = CNC_CHAT
    context.message.source_uuid = USER_1
    context.message.text = "Hello"

    await motd.handle(context)

    # no side effects!
    assert not context.send.called
    assert not motd.gm.get_members.called
    assert not motd.gm.put_members.called
    assert not motd.gm.retain_only.called


async def test_null_update(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT
    context.message.source_uuid = USER_1

    await motd.handle(context)

    assert context.send.called
    assert SOCIAL_CHAT_NAME in context.send.call_args.args[0]
    motd.gm.put_members.assert_called_with(SOCIAL_CHAT, SOCIAL_CHAT_MEMBERS)
    motd.gm.retain_only.assert_called_with(GROUPS)


async def test_new_user(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT
    context.message.source_uuid = USER_1

    NEW_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    motd.bot._groups_by_internal_id[SOCIAL_CHAT]["members"] = NEW_LIST

    await motd.handle(context)

    assert context.send.called
    assert "welcome" in context.send.call_args.args[0]
    assert USER_2 in context.send.call_args.args[0]
    motd.gm.put_members.assert_called_with(SOCIAL_CHAT, NEW_LIST)
    motd.gm.retain_only.assert_called_with(GROUPS)


async def test_removed_user(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT
    context.message.source_uuid = USER_1

    OLD_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    motd.gm.get_members = MagicMock(return_value=OLD_LIST)

    await motd.handle(context)

    assert context.send.called
    assert "goodbye" in context.send.call_args.args[0]
    assert USER_2 in context.send.call_args.args[0]
    motd.gm.put_members.assert_called_with(SOCIAL_CHAT, SOCIAL_CHAT_MEMBERS)
    motd.gm.retain_only.assert_called_with(GROUPS)


async def test_removed_group(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT
    context.message.source_uuid = USER_1

    del motd.bot._groups_by_internal_id[CNC_CHAT]
    
    await motd.handle(context)

    motd.gm.put_members.assert_called_with(SOCIAL_CHAT, SOCIAL_CHAT_MEMBERS)
    motd.gm.retain_only.assert_called_with([SOCIAL_CHAT])


async def test_new_group(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT
    context.message.source_uuid = USER_1

    NEW_GROUPS = GROUPS + [ NEW_CHAT ]
    motd.bot._groups_by_internal_id[NEW_CHAT] = {
        'name' : 'new name',
        'members': [],
    }
    
    await motd.handle(context)

    motd.gm.retain_only.assert_called_with(NEW_GROUPS)