import logging
import pytest
import random
from types import SimpleNamespace
from unittest.mock import MagicMock

from welcomebot import update_group

logger = logging.getLogger("store_test")

UNCHANGED_GROUP = {
    'name': 'unchanged',
    'internal_id': 'UNCHANGED',
    'members': [ 'a', 'b', 'c'],
    'stored': [ 'a', 'b', 'c'],
}

NEW_MEMBER_GROUP = {
    'name': 'added',
    'internal_id': 'NEW_MEMBER',
    'members': [ 'a', 'b', 'c'],
    'stored': [ 'a', 'c'],
}

REMOVED_MEMBER_GROUP = {
    'name': 'removed',
    'internal_id': 'REMOVED_MEMBER',
    'members': [ 'a', 'c'],
    'stored': [ 'a', 'b', 'c'],
}

GROUPS = {
    UNCHANGED_GROUP['name']: UNCHANGED_GROUP,
    NEW_MEMBER_GROUP['name']: NEW_MEMBER_GROUP,
    REMOVED_MEMBER_GROUP['name']: REMOVED_MEMBER_GROUP,
}


def bot_get_group(*args, **kwargs):
    ret = None
    group = args[0]
    if not group in GROUPS:
        return None
    else:
        return GROUPS[group]


def store_get_members(*args, **kwargs):
    ret = None
    group = args[0]
    if not group in GROUPS:
        return None
    else:
        ret = GROUPS[group]['stored'] 
        random.shuffle(ret)
        return ret


@pytest.fixture
def store():
    fake_store = SimpleNamespace()
    fake_store.get_members = MagicMock(side_effect=store_get_members)
    fake_store.retain_only = MagicMock()
    fake_store.put_members = MagicMock()
    return fake_store


@pytest.fixture
def bot():
    fake_bot = SimpleNamespace()
    fake_bot.get_group = MagicMock(side_effect=bot_get_group)
    fake_bot.groups = GROUPS.values()
    return fake_bot


async def test_null_members(bot, store):
    assert not await update_group(logger, bot, "foo", store)
    store.put_members.assert_not_called()
    assert "foo" not in store.retain_only.call_args.args
    for g in GROUPS.values():
        assert g['internal_id'] in store.retain_only.call_args.args[0]


async def test_same_members(bot, store):
    assert not await update_group(logger, bot, UNCHANGED_GROUP['name'], store)
    store.put_members.assert_called_once()
    store.put_members.retain_only()


async def test_new_members(bot, store):
    assert await update_group(logger, bot, NEW_MEMBER_GROUP['name'], store)
    store.put_members.assert_called_once()
    store.put_members.retain_only()


async def test_removed_members(bot, store):
    assert not await update_group(logger, bot, REMOVED_MEMBER_GROUP['name'], store)
    store.put_members.assert_called_once()
    store.put_members.retain_only()
