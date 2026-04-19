import logging
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock, MagicMock

from signalbot import MessageType
from welcomebot import CNCCommand

USER = "user 1"
MANAGER_1 = "user 2"
MANAGER_2 = "user 3"
MANAGERS = [MANAGER_1, MANAGER_2]

CHAT_1_NAME = "chat1"
CHAT_1_ID = "aabbfgfg_chat1"
CHAT_1_TAG = "aabbfgf" # sorts to group 1
GROUP_1 = {
    'name' : CHAT_1_NAME,
    'internal_id' : CHAT_1_ID,
    'members' : MANAGERS,
}
CHAT_2_NAME = "chat2"
CHAT_2_ID = "aabbfggf_chat2"
CHAT_2_TAG = "aabbfgg" # sorts to group 2
GROUP_2 = {
    'name' : CHAT_2_NAME,
    'internal_id' : CHAT_2_ID,
    'members': [],
}
GROUPS = [GROUP_1, GROUP_2]
GROUP_IDS = [ CHAT_1_ID, CHAT_2_ID ]

CNC_ID = CHAT_1_ID

MOTD = """This is a 
multiline "message"
with some emoji:  👋👋"""

TOS = """I'm a little teapot"""

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
    fake_groups.list_groups = MagicMock(return_value=GROUPS)
    fake_groups.get_members = MagicMock(return_value=MANAGERS)
    fake_groups.put_members = MagicMock()
    fake_groups.retain_only = MagicMock()
    fake_groups.put_motd = MagicMock()
    fake_groups.get_motd = MagicMock()
    fake_groups.has_group = MagicMock(return_value=True)

    fake_bot = SimpleNamespace()
    fake_bot.get_group = MagicMock(side_effect=GROUPS)
    fake_bot.groups = GROUPS

    cnc = CNCCommand(
        logger,
        MANAGERS,
        CNC_ID,
        fake_groups)
    cnc.bot = fake_bot
    return cnc


async def test_hello_1(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = "Hello"

    await cnc.handle(context)

    assert len(context.send.call_args.args) == 1
    assert "help" in context.send.call_args.args[0]


async def test_hello_2(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_2
    context.message.text = "Hello"

    await cnc.handle(context)

    assert len(context.send.call_args.args) == 1
    assert "help" in context.send.call_args.args[0]


async def test_reject_dm(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = None
    context.message.source_uuid = USER
    context.message.text = "Hello"

    await cnc.handle(context)
    
    context.send.assert_not_called()


async def test_reject_user(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = USER
    context.message.text = "Hello"

    await cnc.handle(context)
    context.send.assert_not_called()


async def test_list(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = "List_groups"

    await cnc.handle(context)

    assert len(context.send.call_args.args) == 1
    assert CHAT_1_NAME in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_clear_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'set_motd 1'

    await cnc.handle(context)
    
    cnc.store.put_motd.assert_called_once_with(CHAT_2_ID, None)

    assert len(context.send.call_args.args) == 1
    assert 'cleared' in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_set_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'set_motd 1\n{MOTD}'

    await cnc.handle(context)
    
    cnc.store.put_motd.assert_called_once_with(CHAT_2_ID, MOTD)

    assert len(context.send.call_args.args) == 1
    assert 'set' in context.send.call_args.args[0]
    assert CHAT_2_NAME in context.send.call_args.args[0]


async def test_set_motd_out_of_range(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'set_motd 10\n{MOTD}'

    await cnc.handle(context)
    
    cnc.store.put_motd.assert_not_called()

    assert len(context.send.call_args.args) == 1
    assert 'range' in context.send.call_args.args[0]


async def test_get_motd_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'set_motd badnum\n{MOTD}'

    await cnc.handle(context)
    
    cnc.store.put_motd.assert_not_called()

    assert len(context.send.call_args.args) == 1
    assert 'invalid' in context.send.call_args.args[0]
    


async def test_get_motd(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'get_motd 1'

    await cnc.handle(context)
    
    cnc.store.get_motd.assert_called_once_with(CHAT_2_ID)


async def test_get_motd_out_of_range(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'get_motd 10'

    await cnc.handle(context)
    
    cnc.store.get_motd.assert_not_called()

    assert len(context.send.call_args.args) == 1
    assert 'range' in context.send.call_args.args[0]


async def test_get_motd_nan(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'get_motd badnum'

    await cnc.handle(context)
    
    cnc.store.get_motd.assert_not_called()

    assert len(context.send.call_args.args) == 1
    assert 'invalid' in context.send.call_args.args[0]
    

async def test_unknwon_cnc_channel(cnc, context):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'get_motd badnum'

    cnc.store.has_group = MagicMock(return_value=False)
    
    await cnc.handle(context)

    cnc.store.put_members.assert_called_with(CNC_ID, MANAGERS)


async def test_clear_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'set_tos'

    await cnc.handle(context)
    
    cnc.store.put_motd.assert_called_once_with('TOS', None)

    assert len(context.send.call_args.args) == 1
    assert 'cleared' in context.send.call_args.args[0]
    assert 'tos' in context.send.call_args.args[0]


async def test_set_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'set_tos\n{TOS}'

    await cnc.handle(context)
    
    cnc.store.put_motd.assert_called_once_with('TOS', TOS)

    assert len(context.send.call_args.args) == 1
    assert 'set' in context.send.call_args.args[0]
    assert 'tos' in context.send.call_args.args[0]


async def test_get_tos(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'get_tos'

    await cnc.handle(context)
    
    cnc.store.get_motd.assert_called_once_with('TOS')


async def test_who(cnc: CNCCommand[logging.Logger, list[str], str, SimpleNamespace], context: SimpleNamespace):
    context.message.type = MessageType.DATA_MESSAGE
    context.message.group = CNC_ID
    context.message.source_uuid = MANAGER_1
    context.message.text = f'who'

    await cnc.handle(context)
    
    assert len(context.send.call_args.args) == 1
    assert MANAGER_1 in context.send.call_args.args[0]
    assert MANAGER_2 in context.send.call_args.args[0]
