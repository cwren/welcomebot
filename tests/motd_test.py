from copy import deepcopy
import logging
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock, MagicMock

from welcomebot import MotDCommand

from .utils import FakeCall, assert_sent_once

from .conftest import FakeGroupDir
from .conftest import MY_NUMBER
from .conftest import OTHER_NUMBER
from .conftest import GROUPS
from .conftest import GROUP_IDS
from .conftest import CNC_CHAT_ID
from .conftest import SOCIAL_GROUP
from .conftest import SOCIAL_CHAT_ID
from .conftest import SOCIAL_CHAT_MEMBERS
from .conftest import NEW_GROUP
from .conftest import NEW_CHAT_ID
from .conftest import NEW_CHAT_MEMBERS
from .conftest import USER_1
from .conftest import USER_2
from .conftest import MOTD

logger = logging.getLogger("motd_test")


def make_mention(number):
    mention = SimpleNamespace()
    mention.number = number
    return mention

@pytest.fixture
def context(bot):
    context = SimpleNamespace()
    context.message = SimpleNamespace()
    context.message.group_info = SimpleNamespace()
    context.message.group_info.group_id = SOCIAL_CHAT_ID
    context.message.source_number = OTHER_NUMBER
    context.message.text_styles = None
    context.message.mentions = []
    context.send = AsyncMock(return_value=3)
    context.bot = bot
    return context



@pytest.fixture
def config():
    config = SimpleNamespace()
    config.logger = logger
    config.welcome_cnc = CNC_CHAT_ID
    config.instant_welcome = True
    return config


@pytest.fixture
def motd(config, bot, store):
    motd = MotDCommand(
        config,
        bot,
        store)
    return motd


@pytest.fixture
def delayed_motd(config, bot, store):
    config.instant_welcome = False
    motd = MotDCommand(
        config,
        bot,
        store)
    return motd


async def test_hello(motd, context):
    context.message.text = "Hello"

    await motd.handle_data_message(context)

    context.send.assert_not_called()


async def test_ignore_self_dm(motd, context):
    context.message.source_number = MY_NUMBER

    await motd.handle_data_message(context)

    context.send.assert_not_called()


async def test_ignore_read_receipt(motd, context):
    await motd.handle_data_message(context)

    context.send.assert_not_called()


async def test_respond_to_mention(motd, context):
    context.message.mentions = [  make_mention(MY_NUMBER) ]

    await motd.handle_data_message(context)



async def test_handle_nonetype_mentions(motd, context):
    context.message.mentions = None

    await motd.handle_data_message(context)

    context.send.assert_not_called()


async def test_respond_with_default_tos(motd, context):
    context.message.mentions = [ make_mention(MY_NUMBER) ]
    motd.store.get_motd = MagicMock(return_value=None)

    await motd.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'simple bot' in context.send.call_args.args[0].text


async def test_reject_dm_with_MOTD(motd, context):
    context.message.group_info.group_id = None
    context.message.text = "Hello"

    await motd.handle_data_message(context)

    assert_sent_once(context, FakeCall(text=MOTD.text))


async def test_reject_dm_generic(motd, context):
    context.message.group_info.group_id = None
    context.message.text = "Hello"
    motd.store.get_motd = MagicMock(return_value=None)

    await motd.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert "group chats" in context.send.call_args.args[0].text


async def test_ignore_empty_dm(motd, context):
    context.message.group_info.group_id = None
    context.message.text = ""
    motd.store.get_motd = MagicMock(return_value=None)

    await motd.handle_data_message(context)
    
    context.send.assert_not_called()


async def test_ignore_missing_text(motd, context):
    context.message.group_info.group_id = None
    context.message.text = None
    motd.store.get_motd = MagicMock(return_value=None)

    await motd.handle_data_message(context)
    
    context.send.assert_not_called()


async def test_ignore_cnc_data(motd, context):
    context.message.group_info.group_id = CNC_CHAT_ID
    context.message.text = "Hello"

    await motd.handle_data_message(context)

    context.send.assert_not_called()


async def test_ignore_cnc_update(motd, context):
    context.message.group_info.group_id = CNC_CHAT_ID
    context.message.text = "Hello"

    await motd.handle_data_message(context)

    # no side effects!
    context.send.assert_not_called()
    motd.store.get_members.assert_not_called()
    motd.store.put_members.assert_not_called()
    motd.store.retain_only.assert_not_called()


async def test_null_update(motd, context):
    context.message.source_uuid = USER_1

    await motd.handle_group_update(context)

    context.send.assert_not_called()


async def test_new_user(motd, context):
    UPDATED_SOCIAL_GROUP = deepcopy(SOCIAL_GROUP)
    NEW_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    UPDATED_SOCIAL_GROUP.members = NEW_LIST
    context.bot.groups = FakeGroupDir([UPDATED_SOCIAL_GROUP])

    await motd.handle_group_update(context)

    assert_sent_once(context, FakeCall(text=MOTD.text))
    motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, NEW_LIST)
    motd.store.retain_only.assert_called_once()


async def test_post_delayed_welcome(delayed_motd, context):
    UPDATED_SOCIAL_GROUP = deepcopy(SOCIAL_GROUP)
    NEW_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    UPDATED_SOCIAL_GROUP.members = NEW_LIST
    context.bot.groups = FakeGroupDir([UPDATED_SOCIAL_GROUP])

    await delayed_motd.handle_group_update(context)

    context.send.assert_not_called()
    delayed_motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, NEW_LIST)
    delayed_motd.store.retain_only.assert_called_once()
    delayed_motd.store.schedule_welcome.assert_called_with(SOCIAL_CHAT_ID)


async def test_send_delayed_welcome(motd, context):
    motd.instant = False
    motd.store.get_outstanding_welcomes = MagicMock(return_value=[])
    motd.store.get_motd_groups = MagicMock(return_value={SOCIAL_CHAT_ID})

    UPDATED_SOCIAL_GROUP = deepcopy(SOCIAL_GROUP)
    NEW_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    UPDATED_SOCIAL_GROUP.members = NEW_LIST
    context.bot.groups = FakeGroupDir([UPDATED_SOCIAL_GROUP])

    await motd.process_queue()

    assert_sent_once(motd.bot.messages, FakeCall(receiver=SOCIAL_CHAT_ID, text=MOTD.text))


async def test_new_user_not_motd(motd, context):
    UPDATED_SOCIAL_GROUP = deepcopy(SOCIAL_GROUP)
    NEW_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    UPDATED_SOCIAL_GROUP.members = NEW_LIST
    context.bot.groups = FakeGroupDir([UPDATED_SOCIAL_GROUP])
    motd.store.get_motd = MagicMock(return_value=None)

    await motd.handle_group_update(context)

    context.send.assert_not_called()
    motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, NEW_LIST)
    motd.store.retain_only.assert_called_once()


async def test_removed_user(motd, context):
    context.message.source_uuid = USER_1

    OLD_LIST = SOCIAL_CHAT_MEMBERS + [ USER_2 ]
    motd.store.get_members = MagicMock(return_value=OLD_LIST)

    await motd.handle_group_update(context)

    context.send.assert_not_called()

    motd.store.put_members.assert_called_with(SOCIAL_CHAT_ID, SOCIAL_CHAT_MEMBERS)
    motd.store.retain_only.assert_called_with(GROUP_IDS)


async def test_removed_group(motd, context):
    context.message.source_uuid = USER_1

    context.bot.groups = FakeGroupDir([SOCIAL_GROUP])
    
    await motd.handle_group_update(context)

    motd.store.retain_only.assert_called_with([SOCIAL_CHAT_ID])


async def test_new_group(motd, context):
    context.message.group_info.group_id = NEW_CHAT_ID
    context.message.source_uuid = USER_1

    NEW_GROUPS = GROUPS + [ NEW_GROUP ]
    NEW_GROUP_IDS = GROUP_IDS + [ NEW_CHAT_ID ] 
    context.bot.groups = FakeGroupDir(NEW_GROUPS)
    
    await motd.handle_group_update(context)

    motd.store.put_members.assert_called_with(NEW_CHAT_ID, NEW_CHAT_MEMBERS)
    motd.store.retain_only.assert_called_with(NEW_GROUP_IDS)
