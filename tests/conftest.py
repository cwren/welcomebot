from copy import deepcopy
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock, MagicMock

from welcomebot import Message, MotDCommand


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
        self.groups = groups
        self.by_name = { g.internal_id: g for g in groups }

    def __iter__(self):
        return self.groups.__iter__()

    def __next__(self):
        return self.groups.__next__()

    def get(self, id):
        return self.by_name.get(id)
    
    
SOCIAL_CHAT_NAME = "socialchat"
SOCIAL_CHAT_MEMBERS = [ USER_1 ]
SOCIAL_CHAT_ID = "socialchatID"
SOCIAL_GROUP = FakeGroup(SOCIAL_CHAT_NAME, SOCIAL_CHAT_ID, SOCIAL_CHAT_MEMBERS)

CNC_CHAT_NAME = "cncchat"
CNC_CHAT_MEMBERS = [ USER_1 ]
CNC_CHAT_ID = "cncchatID"
CNC_GROUP = FakeGroup(CNC_CHAT_NAME, CNC_CHAT_ID, CNC_CHAT_MEMBERS)

NEW_CHAT_NAME = "newchat"
NEW_CHAT_MEMBERS = [ USER_1, USER_2 ]
NEW_CHAT_ID = "newchatID"
NEW_GROUP = FakeGroup(NEW_CHAT_NAME, NEW_CHAT_ID, NEW_CHAT_MEMBERS)

GROUPS = [ CNC_GROUP, SOCIAL_GROUP ]
GROUP_IDS = [ CNC_CHAT_ID, SOCIAL_CHAT_ID ]

MOTD = Message("This is a message")

@pytest.fixture
def bot():
    fake_bot = SimpleNamespace()
    fake_bot.groups = FakeGroupDir(GROUPS)
    fake_bot.config = SimpleNamespace()
    fake_bot.messages = SimpleNamespace()
    fake_bot.messages.send = AsyncMock()
    fake_bot.config.phone_number = MY_NUMBER
    return fake_bot


@pytest.fixture
def store():
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
    return fake_store