from datetime import datetime, UTC
from importlib.metadata import version
import logging
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock, MagicMock

from welcomebot import Attachment, Calendar, CNCCommand, Message, Reminder

from .utils import assert_sent_once

USER = "user 1"
MANAGER_1 = "user 2"
MANAGER_2 = "user 3"
MANAGERS = [MANAGER_1, MANAGER_2]

CHAT_1_NAME = "chat1"
CHAT_1_ID = "aabbfgfg_chat1"
CHAT_1_TAG = "37C3D"
GROUP_1 = {
    'name' : CHAT_1_NAME,
    'internal_id' : CHAT_1_ID,
    'members' : MANAGERS,
}
CHAT_2_NAME = "chat2"
CHAT_2_ID = "aabbfggf_chat2"
CHAT_2_TAG = "CD3DE"
GROUP_2 = {
    'name' : CHAT_2_NAME,
    'internal_id' : CHAT_2_ID,
    'members': [],
}
GROUPS = [GROUP_1, GROUP_2]
GROUP_IDS = [ CHAT_1_ID, CHAT_2_ID ]

CNC_ID = CHAT_1_ID

MOTD = Message("""This is a 
multiline "message"
with some emoji:  👋👋""")

TOS = Message("I'm a little teapot")
REMINDER_1_MSG = Message("This is my handle")
REMINDER_2_MSG = Message("this is my spout")

DATE = [ 2026, 5, 26, 16, 47, 10, 1, UTC ]
TODAY = 2461187
REMINDER_1_DATE = '2026-05-26'
REMINDER_1 = Reminder(CHAT_1_ID, TODAY, 7, REMINDER_1_MSG, id=1)
REMINDER_2_DATE = '2026-05-31'
REMINDER_2 = Reminder(CHAT_2_ID, TODAY + 5, 28, REMINDER_2_MSG, id=2)

logger = logging.getLogger("cnc_test")


@pytest.fixture
def cal():
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=datetime(*DATE))
    return Calendar(dt=dt)

@pytest.fixture
def context():
    context = SimpleNamespace()
    context.message = SimpleNamespace()
    context.message.group_info = SimpleNamespace()
    context.message.group_info.group_id = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.attachments_local_filenames = []
    context.message.text_styles = None
    
    context.send = AsyncMock(return_value=3)
    return context

@pytest.fixture
def store():
    fake_store = SimpleNamespace()
    fake_store.list_groups = MagicMock(return_value=GROUPS)
    fake_store.get_members = MagicMock(return_value=MANAGERS)
    fake_store.put_members = MagicMock()
    fake_store.retain_only = MagicMock()
    fake_store.put_motd = MagicMock()
    fake_store.get_motd = MagicMock()
    fake_store.has_group = MagicMock(return_value=True)
    fake_store.put_reminder = MagicMock(return_value=REMINDER_1.id)
    fake_store.get_reminder = MagicMock(return_value=REMINDER_1)
    fake_store.get_all_reminders = MagicMock(return_value=[REMINDER_1, REMINDER_2])
    fake_store.delete_reminder = MagicMock()
    return fake_store

@pytest.fixture
def bot():
    fake_bot = SimpleNamespace()
    fake_bot.get_group = MagicMock(side_effect=GROUPS)
    fake_bot.groups = GROUPS
    return fake_bot

@pytest.fixture
def reminders():
    fake_reminders = SimpleNamespace()
    fake_reminders.process_queue = AsyncMock()
    return fake_reminders

@pytest.fixture
def config():
    fake_config = SimpleNamespace()
    fake_config.logger = logger
    fake_config.welcome_managers = MANAGERS
    fake_config.welcome_cnc = CNC_ID
    fake_config.to_strings = MagicMock(return_value=['config values'])
    return fake_config

@pytest.fixture
def cnc(config, bot, store, reminders, cal):
    cnc = CNCCommand(
        config,
        store,
        reminders,
        cal)
    cnc.bot = bot
    return cnc


async def test_hello_1(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = "Hello"

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert "help" in context.send.call_args.args[0].text


async def test_hello_2(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.source_uuid = MANAGER_2
    context.message.text = "Hello"

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert "help" in context.send.call_args.args[0].text


async def test_reject_dm(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.group_info = None
    context.message.source_uuid = USER
    context.message.text = "Hello"

    await cnc.handle_data_message(context)
    
    context.send.assert_not_called()


async def test_reject_user(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.source_uuid = USER
    context.message.text = "Hello"

    await cnc.handle_data_message(context)
    context.send.assert_not_called()


async def test_help(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = "HeLp"

    await cnc.handle_data_message(context)

    assert_sent_once(context, text=CNCCommand.HELP_MESSAGE.text)


async def test_list(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = "List_groups"

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert CHAT_1_NAME in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_group_id(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_group_id {CHAT_2_TAG}'

    await cnc.handle_data_message(context)
    
    assert len(context.send.call_args.args) == 1
    assert CHAT_2_NAME in context.send.call_args.args[0]
    assert CHAT_2_ID in context.send.call_args.args[0]


async def test_group_id_no_group(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = 'get_group_id'

    await cnc.handle_data_message(context)
    
    assert len(context.send.call_args.args) == 1
    assert "unrecognized" in context.send.call_args.args[0]


async def test_group_id_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = 'get_group_id NOTAGROUP'

    await cnc.handle_data_message(context)
    
    assert len(context.send.call_args.args) == 1
    assert "invalid" in context.send.call_args.args[0]


async def test_set_motd_no_group(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_motd'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'unrecognized' in context.send.call_args.args[0]


async def test_set_motd_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_motd NONE_GROUP'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'invalid' in context.send.call_args.args[0]
    assert 'NONE_GROUP' in context.send.call_args.args[0]


async def test_clear_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_motd {CHAT_2_TAG}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_motd.assert_called_once_with(CHAT_2_ID, None)

    assert len(context.send.call_args.args) == 1
    assert 'cleared' in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_set_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_motd {CHAT_2_TAG}\n{MOTD.text}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_motd.assert_called_once_with(CHAT_2_ID, MOTD)

    assert len(context.send.call_args.args) == 1
    assert 'set' in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_set_rich_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_motd {CHAT_2_TAG}\n{MOTD.text}'
    context.message.attachments_local_filenames = ['foo']
    context.message.base64_attachments = ['0000']
    rich = Message(MOTD.text, [Attachment('foo', '0000')])

    await cnc.handle_data_message(context)
    
    cnc.store.put_motd.assert_called_once_with(CHAT_2_ID, rich)

    assert len(context.send.call_args.args) == 1
    assert 'set' in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_get_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_motd {CHAT_2_TAG}\n{MOTD.text}'
    message = Message("THIS IS A TEST MOTD")
    cnc.store.get_motd = MagicMock(return_value=message)

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_called_once_with(CHAT_2_ID)

    assert len(context.send.call_args.args) == 1
    assert message.text in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]
    assert CHAT_2_TAG in context.send.call_args.args[0]


async def test_get_rich_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_motd {CHAT_2_TAG}\n{MOTD.text}'
    rich = Message(MOTD.text, [Attachment('foo', '0000')])
    cnc.store.get_motd = MagicMock(return_value=rich)

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_called_once_with(CHAT_2_ID)

    assert len(context.send.call_args.args) == 1
    assert rich.text in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]
    assert CHAT_2_TAG in context.send.call_args.args[0]
    assert '0000' == context.send.call_args.kwargs['base64_attachments'][0]


async def test_get_motd_null(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_motd {CHAT_2_TAG}\n{MOTD}'
    cnc.store.get_motd = MagicMock(return_value=None)

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_called_once_with(CHAT_2_ID)

    assert len(context.send.call_args.args) == 1
    assert 'no motd' in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]
    assert CHAT_2_TAG in context.send.call_args.args[0]


async def test_get_motd_no_group(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_motd'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'unrecognized' in context.send.call_args.args[0]


async def test_get_motd_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_motd badnum\n{MOTD}'

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_not_called()

    assert len(context.send.call_args.args) == 1
    assert 'invalid' in context.send.call_args.args[0]


async def test_clear_motd_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_motd badnum'

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_not_called()

    assert len(context.send.call_args.args) == 1
    assert 'invalid' in context.send.call_args.args[0]
    

async def test_unknown_cnc_channel(cnc, context):
    
    context.message.text = f'get_motd badnum'

    cnc.store.has_group = MagicMock(return_value=False)
    
    await cnc.handle_data_message(context)

    cnc.store.put_members.assert_called_with(CNC_ID, MANAGERS)


async def test_clear_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_tos'

    await cnc.handle_data_message(context)
    
    cnc.store.put_motd.assert_called_once_with('TOS', None)

    assert len(context.send.call_args.args) == 1
    assert 'cleared' in context.send.call_args.args[0]
    assert 'tos' in context.send.call_args.args[0]


async def test_set_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_tos\n{TOS.text}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_motd.assert_called_once_with('TOS', TOS)

    assert len(context.send.call_args.args) == 1
    assert 'set' in context.send.call_args.args[0]
    assert 'tos' in context.send.call_args.args[0]


async def test_set_rich_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_tos\n{TOS.text}'
    context.message.attachments_local_filenames = ['foo']
    context.message.base64_attachments = ['0000']
    rich = Message(TOS.text, [Attachment('foo', '0000')])

    await cnc.handle_data_message(context)
    
    cnc.store.put_motd.assert_called_once_with('TOS', rich)

    assert len(context.send.call_args.args) == 1
    assert 'set' in context.send.call_args.args[0]
    assert 'tos' in context.send.call_args.args[0]


async def test_get_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_tos'
    cnc.store.get_motd = MagicMock(return_value=TOS)

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_called_once_with('TOS')
    assert len(context.send.call_args.args) == 1
    assert 'tos is' in context.send.call_args.args[0]


async def test_get_rich_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_tos'
    rich = Message(MOTD.text, [Attachment('foo', '0000')])
    cnc.store.get_motd = MagicMock(return_value=rich)

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_called_once_with('TOS')
    assert len(context.send.call_args.args) == 1
    assert 'tos is' in context.send.call_args.args[0]
    assert '0000' == context.send.call_args.kwargs['base64_attachments'][0]


async def test_get_tos_null(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_tos'
    cnc.store.get_motd = MagicMock(return_value=None)

    await cnc.handle_data_message(context)
    
    cnc.store.get_motd.assert_called_once_with('TOS')
    assert len(context.send.call_args.args) == 1
    assert 'there is no tos' in context.send.call_args.args[0]


async def test_set_reminder_no_interval(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'unrecognized' in context.send.call_args.args[0]


async def test_set_reminder_no_group(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'unrecognized' in context.send.call_args.args[0]


async def test_set_reminder_bad_group(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder NOTAGROUP 0 {REMINDER_1.interval}\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'invalid group index' in context.send.call_args.args[0]


async def test_set_reminder_nan_delay(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} foo {REMINDER_1.interval}\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'integer delay' in context.send.call_args.args[0]


async def test_set_reminder_neg_delay(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} -5 {REMINDER_1.interval}\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'negative' in context.send.call_args.args[0]


async def test_set_reminder_nan_period(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0 foo\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'integer interval' in context.send.call_args.args[0]


async def test_set_reminder_neg_period(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0 -5\n{TOS}'

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'negative' in context.send.call_args.args[0]


async def test_set_reminder_backend_fail(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0 {REMINDER_1.interval}\n{TOS}'
    cnc.store.put_reminder = MagicMock(return_value=None)

    await cnc.handle_data_message(context)
    
    cnc.store.put_reminder.assert_called_once()
    assert len(context.send.call_args.args) == 1
    assert 'fail' in context.send.call_args.args[0]


async def test_set_reminder(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0 {REMINDER_1.interval}\n{REMINDER_1_MSG.text}'

    await cnc.handle_data_message(context)
    
    assert len(cnc.store.put_reminder.call_args.args) == 1
    cnc.store.put_reminder.assert_called_once()
    actual = cnc.store.put_reminder.call_args.args[0]
    assert actual.id == Reminder.DRAFT 
    actual.id = REMINDER_1.id 
    assert REMINDER_1 == actual

    assert len(context.send.call_args.args) == 1
    assert f'reminder set: {REMINDER_1.id}' == context.send.call_args.args[0]


async def test_set_rich_reminder(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0 {REMINDER_1.interval}\n{TOS.text}'
    context.message.attachments_local_filenames = ['foo']
    context.message.base64_attachments = ['0000']
    rich_message = Message(TOS.text, [Attachment('foo', '0000')])
    rich = Reminder(CHAT_1_ID, TODAY, 7, rich_message, id=1)

    await cnc.handle_data_message(context)
    
    assert len(cnc.store.put_reminder.call_args.args) == 1
    cnc.store.put_reminder.assert_called_once()
    actual = cnc.store.put_reminder.call_args.args[0]
    assert actual.id == Reminder.DRAFT 
    actual.id = rich.id 
    assert rich == actual

    assert len(context.send.call_args.args) == 1
    assert f'reminder set: {REMINDER_1.id}' == context.send.call_args.args[0]


async def test_set_reminder_in_past(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} -10 {REMINDER_1.interval}\n{TOS}'

    await cnc.handle_data_message(context)

    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'negative' in context.send.call_args.args[0]


async def test_set_reminder_neg_interval(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'set_reminder {CHAT_1_TAG} 0 -10 \n{TOS}'

    await cnc.handle_data_message(context)

    cnc.store.put_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'negative' in context.send.call_args.args[0]


async def test_get_reminder_no_id(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_reminder'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'unrecognized' in  context.send.call_args.args[0]


async def test_get_reminder_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_reminder foo'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'integer index' in  context.send.call_args.args[0]


async def test_get_reminder_null(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_reminder 1'
    cnc.store.get_reminder = MagicMock(return_value=None)

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'could not find' in  context.send.call_args.args[0]


async def test_get_reminder(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_reminder {REMINDER_1.id}'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert str(REMINDER_1.id) in  context.send.call_args.args[0]
    assert REMINDER_1.message.text in  context.send.call_args.args[0]


async def test_get_rich_reminder(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'get_reminder {REMINDER_1.id}'
    rich_message = Message(REMINDER_1_MSG.text, [Attachment('foo', '0000')])
    rich = Reminder(CHAT_1_ID, TODAY, 7, rich_message, id=REMINDER_1.id)
    cnc.store.get_reminder = MagicMock(return_value=rich)

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert str(REMINDER_1.id) in  context.send.call_args.args[0]
    assert REMINDER_1.message.text in  context.send.call_args.args[0]
    assert '0000' == context.send.call_args.kwargs['base64_attachments'][0]


async def test_list_reminders(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = 'list_reminders'

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert str(REMINDER_1.id) in context.send.call_args.args[0]
    assert CHAT_1_NAME in context.send.call_args.args[0]
    assert REMINDER_1_DATE in context.send.call_args.args[0]
    assert REMINDER_1_MSG.text[0:20] in context.send.call_args.args[0]
    assert str(REMINDER_2.id) in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]
    assert REMINDER_2_DATE in context.send.call_args.args[0]
    assert REMINDER_2_MSG.text[0:20] in context.send.call_args.args[0]


async def test_list_reminders_null(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = 'list_reminders'
    cnc.store.get_all_reminders = MagicMock(return_value=[])

    await cnc.handle_data_message(context)

    assert len(context.send.call_args.args) == 1
    assert 'there are no reminders' in  context.send.call_args.args[0]


async def test_delete_reminder_no_id(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'delete_reminder'

    await cnc.handle_data_message(context)

    cnc.store.delete_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'unrecognized' in  context.send.call_args.args[0]


async def test_delete_reminder_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'delete_reminder foo'

    await cnc.handle_data_message(context)

    cnc.store.delete_reminder.assert_not_called()
    assert len(context.send.call_args.args) == 1
    assert 'integer index' in  context.send.call_args.args[0]


async def test_delete_reminder(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'delete_reminder {REMINDER_2.id}'

    await cnc.handle_data_message(context)

    cnc.store.delete_reminder.assert_called_once_with(REMINDER_2.id) 


async def test_who(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'who'

    await cnc.handle_data_message(context)
    
    assert len(context.send.call_args.args) == 1
    assert MANAGER_1 in context.send.call_args.args[0]
    assert MANAGER_2 in context.send.call_args.args[0]


async def test_version(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'version'

    await cnc.handle_data_message(context)
    
    assert len(context.send.call_args.args) == 1
    assert version('welcomebot') in context.send.call_args.args[0]
    assert 'config values' in context.send.call_args.args[0]


async def test_today(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'today'

    await cnc.handle_data_message(context)
    
    assert len(context.send.call_args.args) == 1
    assert str(TODAY) in context.send.call_args.args[0]


async def test_queue(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    
    context.message.text = f'run_reminder_queue'

    await cnc.handle_data_message(context)
    
    cnc.reminders.process_queue.assert_called_once()