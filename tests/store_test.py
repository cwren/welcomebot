import logging
import pytest
import tempfile

from welcomebot import BotStore


USER_1 = "user1"
USER_2 = "user2"
CNC_CHAT = "cncchatID"
SOCIAL_CHAT = "socialchatID"

logger = logging.getLogger("welcomebot")


@pytest.fixture
def store():
    with tempfile.NamedTemporaryFile(mode='w+t', delete=True) as temp_file:
        yield BotStore(logger, temp_file.name)


async def test_null_members(store):
    assert not store.get_members(SOCIAL_CHAT) 


async def test_store_member(store):
    store.put_members(SOCIAL_CHAT, [ USER_1 ])
    ret = store.get_members(SOCIAL_CHAT)
    assert len(ret) == 1
    assert USER_1 in ret
    assert not store.get_members(CNC_CHAT)


async def test_store_members(store):
    store.put_members(SOCIAL_CHAT, [ USER_1, USER_2])
    ret = store.get_members(SOCIAL_CHAT)
    assert len(ret) == 2
    assert USER_1 in ret
    assert USER_2 in ret


async def test_null_motd(store):
    assert not store.get_motd(SOCIAL_CHAT) 


async def test_store_motd(store):
    message = "This is a the Message of the Day"
    store.put_motd(SOCIAL_CHAT, message)
    assert store.get_motd(SOCIAL_CHAT) == message
    assert not store.get_motd(CNC_CHAT)


async def test_store_motd_with_special_characters(store):
    message = 'This is a the "Message of the Day" 👋👋 '
    store.put_motd(SOCIAL_CHAT, message)
    assert store.get_motd(SOCIAL_CHAT) == message