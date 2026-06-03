from datetime import datetime, UTC
import logging
import pytest
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

from welcomebot import BotStore, Calendar, Reminder


USER_1 = "user1"
USER_2 = "user2"
CNC_CHAT = "cncchatID"
SOCIAL_CHAT = "socialchatID"

DATE = [ 2026, 5, 26, 16, 47, 10, 1, UTC ]
TODAY = 2461187
TOMORROW = TODAY + 1
YESTERDAY = TODAY - 1

logger = logging.getLogger("welcomebot")


@pytest.fixture
def cal():
    now = datetime(*DATE)
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=now)
    return Calendar(dt)

@pytest.fixture
def store(cal):
    with tempfile.NamedTemporaryFile(mode='w+t', delete=True) as temp_file:
        yield BotStore(logger, temp_file.name, cal=cal)


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
    
async def test_store_has_group(store):
    assert not store.has_group(SOCIAL_CHAT)
    store.put_members(SOCIAL_CHAT, [ USER_1, USER_2])
    assert store.has_group(SOCIAL_CHAT)
    assert not store.has_group(CNC_CHAT)

async def test_null_reminders(store):
    assert not store.get_all_reminders() 

async def test_create_one_reminder_tomorrow(store):
    message = 'Please brush your teeth 🪥'
    id = store.put_reminder(Reminder(SOCIAL_CHAT, TOMORROW, 7, message))
    
    rows = store.get_all_reminders() 
    assert len(rows) == 1
    assert rows[0].id == id
    assert rows[0].group_id == SOCIAL_CHAT
    assert rows[0].next == TOMORROW
    assert rows[0].interval== 7
    assert rows[0].message == message
    
    assert not store.get_due_reminders()


async def test_get_reminder(store):
    message = 'Please brush your teeth 🪥'
    id = store.put_reminder(Reminder(SOCIAL_CHAT, TOMORROW, 7, message))
    
    reminder = store.get_reminder(id) 
    assert reminder
    assert reminder.id == id
    assert reminder.group_id == SOCIAL_CHAT
    assert reminder.next == TOMORROW
    assert reminder.interval== 7
    assert reminder.message == message


async def test_get_null_reminder(store):
    reminder = store.get_reminder(1000) 
    assert not reminder


async def test_create_one_reminder_yesterday(store):
    message = 'Please brush your teeth 🪥'
    id = store.put_reminder(Reminder(SOCIAL_CHAT, YESTERDAY, 7, message))
    
    rows = store.get_due_reminders() 
    assert len(rows) == 1
    assert rows[0].id == id

async def test_delete_reminder(store):
    message = 'Please brush your teeth 🪥'
    id1 = store.put_reminder(Reminder(SOCIAL_CHAT, YESTERDAY, 7, message))
    id2 = store.put_reminder(Reminder(SOCIAL_CHAT, TODAY, 14, message))
    id3 = store.put_reminder(Reminder(SOCIAL_CHAT, TOMORROW, 30, message))
    
    store.delete_reminder(id2)

    rows = store.get_all_reminders() 
    assert len(rows) == 2
    remaining_ids = [ row.id for row in rows ]
    assert id1 in remaining_ids
    assert id2 not in remaining_ids
    assert id3 in remaining_ids

async def test_delete_null_reminder(store):
    message = 'Please brush your teeth 🪥'
    id1 = store.put_reminder(Reminder(SOCIAL_CHAT, YESTERDAY, 7, message))
    id2 = store.put_reminder(Reminder(SOCIAL_CHAT, TODAY, 14, message))
    id3 = store.put_reminder(Reminder(SOCIAL_CHAT, TOMORROW, 30, message))
    
    store.delete_reminder(1000)

    rows = store.get_all_reminders() 
    assert len(rows) == 3
    remaining_ids = [ row.id for row in rows ]
    assert id1 in remaining_ids
    assert id2 in remaining_ids
    assert id3 in remaining_ids

async def test_get_due_reminders(store):
    message = 'Please brush your teeth 🪥'
    id1 = store.put_reminder(Reminder(SOCIAL_CHAT, YESTERDAY, 7, message))
    id2 = store.put_reminder(Reminder(SOCIAL_CHAT, TODAY, 14, message))
    id3 = store.put_reminder(Reminder(SOCIAL_CHAT, TOMORROW, 30, message))

    rows = store.get_due_reminders() 
    assert len(rows) == 2
    due_ids = [ row.id for row in rows ]
    assert id1 in due_ids
    assert id2 in due_ids
    assert id3 not in due_ids

async def test_update_reminders(store):
    message = 'Please brush your teeth 🪥'
    id = store.put_reminder(Reminder(SOCIAL_CHAT, YESTERDAY, 7, message))
    store.repost_reminder(id)
    
    assert not store.get_due_reminders()

    rows = store.get_all_reminders() 
    assert len(rows) == 1
    assert rows[0].id == id
    assert rows[0].next == YESTERDAY + 7