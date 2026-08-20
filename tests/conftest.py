from copy import deepcopy
from datetime import datetime, UTC
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock, MagicMock

from welcomebot import Message, Calendar


USER_1 = "user1"
USER_2 = "user2"
MY_NUMBER = "+1234567890"
OTHER_NUMBER = "+0987654321"

class FakeGroup():
    def __init__(self, name, id, members, stored=None):
        self.name = name
        self.internal_id = id
        self.members = deepcopy(members)
        self.stored = deepcopy(stored) if stored else deepcopy(members)

class FakeGroupDir():
    def __init__(self, groups):
        self.groups = deepcopy(groups)
        self.by_name = { g.internal_id: deepcopy(g) for g in groups }

    def __iter__(self):
        return self.groups.__iter__()

    def __next__(self):
        return self.groups.__next__()

    def get(self, id):
        return self.by_name.get(id)

# {'name': 'cncchat', 'internal_id': 'cncchatID', 'tag': '21A9E'}
# {'name': 'socialchat', 'internal_id': 'socialchatID', 'tag': '610EA'}

MANAGER_1 = "manager_1"
MANAGER_2 = "manager_2"
MANAGERS = [MANAGER_1, MANAGER_2]

SOCIAL_CHAT_NAME = "socialchat"
SOCIAL_CHAT_MEMBERS = [ USER_1 ]
SOCIAL_CHAT_ID = "socialchatID"
SOCIAL_CHAT_TAG = "610EA"
SOCIAL_GROUP = FakeGroup(SOCIAL_CHAT_NAME, SOCIAL_CHAT_ID, SOCIAL_CHAT_MEMBERS)

CNC_CHAT_NAME = "cncchat"
CNC_CHAT_MEMBERS = [ MANAGER_1, MANAGER_2 ]
CNC_CHAT_ID = "cncchatID"
CNC_CHAT_TAG = "21A9E"
CNC_GROUP = FakeGroup(CNC_CHAT_NAME, CNC_CHAT_ID, CNC_CHAT_MEMBERS)

NEW_CHAT_NAME = "newchat"
NEW_CHAT_MEMBERS = [ USER_1, USER_2 ]
NEW_CHAT_ID = "newchatID"
NEW_GROUP = FakeGroup(NEW_CHAT_NAME, NEW_CHAT_ID, NEW_CHAT_MEMBERS)

GROUPS = [ CNC_GROUP, SOCIAL_GROUP ]
GROUP_IDS = [ CNC_CHAT_ID, SOCIAL_CHAT_ID ]

MOTD = Message("This is a message")

DATE = [ 2026, 5, 26, 16, 47, 10, 1, UTC ]
TODAY = 2461187

@pytest.fixture
def cal():
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=datetime(*DATE))
    return Calendar(dt=dt)

@pytest.fixture
def bot(scope="function", autouse=True):
    fake_bot = SimpleNamespace()
    fake_bot.groups = FakeGroupDir(GROUPS)
    fake_bot.config = SimpleNamespace()
    fake_bot.messages = SimpleNamespace()
    fake_bot.messages.send = AsyncMock()
    fake_bot.config.phone_number = MY_NUMBER
    return fake_bot


@pytest.fixture
def store(scope="function", autouse=True):
    fake_store = SimpleNamespace()
    fake_store.list_groups = MagicMock(return_value=GROUPS)
    fake_store.get_members = MagicMock(return_value=SOCIAL_CHAT_MEMBERS)
    fake_store.put_members = MagicMock()
    fake_store.retain_only = MagicMock()
    fake_store.get_motd = MagicMock(return_value=MOTD)
    fake_store.has_group = MagicMock(return_value=True)
    fake_store.schedule_welcome = MagicMock()
    fake_store.get_outstanding_welcomes = MagicMock()
    fake_store.remove_welcomes_for = MagicMock()
    fake_store.put_motd = MagicMock()
    fake_store.put_reminder = MagicMock()
    fake_store.get_reminder = MagicMock()
    fake_store.get_all_reminders = MagicMock()
    fake_store.delete_reminder = MagicMock()
    return fake_store