from copy import deepcopy
import logging
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock, MagicMock

from signalbot import MessageType
from welcomebot import MotDCommand

USER_1 = "user1"
USER_2 = "user2"

SOCIAL_CHAT_NAME = "socialchat"
SOCIAL_CHAT_MEMBERS = [ USER_1 ]
SOCIAL_CHAT_ID = "socialchatID"
SOCIAL_GROUP = {
    'name' : SOCIAL_CHAT_NAME,
    'members' : SOCIAL_CHAT_MEMBERS,
    'internal_id' : SOCIAL_CHAT_ID,
}
CNC_CHAT_NAME = "cncchat"
CNC_CHAT_MEMBERS = [ USER_1 ]
CNC_CHAT_ID = "cncchatID"
CNC_GROUP = {
    'name' : CNC_CHAT_NAME,
    'members' : CNC_CHAT_MEMBERS,
    'internal_id' : CNC_CHAT_ID,
}
NEW_CHAT_NAME = "newchat"
NEW_CHAT_MEMBERS = [ USER_1, USER_2 ]
NEW_CHAT_ID = "newchatID"
NEW_GROUP = {
    'name' : NEW_CHAT_NAME,
    'members' : NEW_CHAT_MEMBERS,
    'internal_id' : NEW_CHAT_ID,
}
GROUPS = [CNC_GROUP, SOCIAL_GROUP]
GROUP_IDS = [ CNC_CHAT_ID, SOCIAL_CHAT_ID ]

MOTD = "This is a message"

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
    fake_groups.get_motd = MagicMock(return_value=MOTD)

    fake_bot = SimpleNamespace()
    fake_bot.get_group = MagicMock(side_effect=[SOCIAL_GROUP, CNC_GROUP])
    fake_bot.groups = GROUPS

    motd = MotDCommand(
        logger,
        CNC_CHAT_ID,
        fake_groups)
    motd.bot = fake_bot
    return motd


async def test_hello(motd, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = SOCIAL_CHAT_ID
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
    context.message.group = CNC_CHAT_ID
    context.message.source_uuid = USER_1
    context.message.text = "Hello"

    await motd.handle(context)

    assert not context.send.called


async def test_ignore_cnc_update(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = CNC_CHAT_ID
    context.message.source_uuid = USER_1
    context.message.text = "Hello"

    await motd.handle(context)

    # no side effects!
    assert not context.send.called
    assert not motd.store.get_members.called
    assert not motd.store.put_members.called
    assert not motd.store.retain_only.called


async def test_null_update(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT_ID
    context.message.source_uuid = USER_1

    await motd.handle(context)

    assert not context.send.called


async def test_new_user(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT_ID
    context.message.source_uuid = USER_1

    UPDATED_SOCIAL_GROUP = deepcopy(SOCIAL_GROUP)
    NEW_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    UPDATED_SOCIAL_GROUP["members"] = NEW_LIST
    motd.bot.get_group = MagicMock(side_effect=[UPDATED_SOCIAL_GROUP])

    await motd.handle(context)

    context.send.assert_called_with(MOTD)
    motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, NEW_LIST)
    motd.store.retain_only.assert_called_once


async def test_removed_user(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT_ID
    context.message.source_uuid = USER_1

    OLD_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    motd.store.get_members = MagicMock(return_value=OLD_LIST)

    await motd.handle(context)

    assert not context.send.called

    motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, SOCIAL_CHAT_MEMBERS)
    motd.store.retain_only.assert_called_with(GROUP_IDS)


async def test_removed_group(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = SOCIAL_CHAT_ID
    context.message.source_uuid = USER_1

    motd.bot.get_group = MagicMock(side_effect=[SOCIAL_GROUP])
    motd.bot.groups = [SOCIAL_GROUP]
    
    await motd.handle(context)

    motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, SOCIAL_CHAT_MEMBERS)
    motd.store.retain_only.assert_called_with([SOCIAL_CHAT_ID])


async def test_new_group(motd, context):
    context.message.type = MessageType.GROUP_UPDATE_MESSAGE
    context.message.group = NEW_CHAT_ID
    context.message.source_uuid = USER_1

    NEW_GROUPS = GROUPS + [ NEW_GROUP ]
    NEW_GROUP_IDS = GROUP_IDS + [ NEW_CHAT_ID ]
    motd.bot.get_group = MagicMock(side_effect=[NEW_GROUP])
    motd.bot.groups = NEW_GROUPS
    
    await motd.handle(context)

    motd.store.put_members.assert_called_with(NEW_CHAT_ID, NEW_CHAT_MEMBERS)
    motd.store.retain_only.assert_called_with(NEW_GROUP_IDS)
