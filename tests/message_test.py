import json
import pytest
from types import SimpleNamespace

from welcomebot import Message, OverlappingStyleRegions, UnknownStyle, apply_styles


def make_style(type, start, length):
    style = SimpleNamespace()
    style.style = type
    style.start = start
    style.length = length
    return style


def set_text(message, text):
    message.text = text


def append_style(message, style):
    if style:
        message.text_styles.append(style)


@pytest.fixture
def message():
    message = SimpleNamespace()
    message.text = ""
    message.text_styles = []
    return message


async def test_constructor():
    attachments = [{'a': 'a'}]
    m = Message('foo', attachments=attachments)
    assert m.text == 'foo'
    assert m.attachments == attachments
    assert not m.mentions
    assert m.has_attachments

    m = Message('foo')
    assert m.text == 'foo'
    assert not m.attachments
    assert not m.mentions
    assert not m.has_attachments

    m = Message('foo', has_attachments=True)
    assert m.text == 'foo'
    assert not m.attachments
    assert not m.mentions
    assert m.has_attachments


async def test_mentions():
    text = 'foo @12345678-1234-1234-1234-1234567890ab or @12345678-1234-1234-1234-1234567890AC'
    mentions = [
        {'start': 4, 'length': 1, 'author': '12345678-1234-1234-1234-1234567890ab'},
        {'start': 9, 'length': 1, 'author': '12345678-1234-1234-1234-1234567890AC'},
    ]
    m = Message(text)
    assert m.text == text
    assert m.send_text == 'foo \uFFFC or \uFFFC'
    assert m.mentions == mentions


async def test_no_styles(message):
    text = "this is a plain message"
    expected = text
    set_text(message, text)

    apply_styles(message)

    assert expected == message.text


async def test_empty_styles(message):
    text = "this is a plain message"
    expected = text
    set_text(message, text)
    append_style(message, None)

    apply_styles(message)

    assert expected == message.text


async def test_bold_style(message):
    text = "this message has a bold word"
    expected = "this message has a **bold** word"
    set_text(message, text)
    append_style(message, make_style('BOLD', 19, 4))

    apply_styles(message)

    assert expected == message.text


async def test_italic_style(message):
    text = "this message has an italic word"
    expected = "this message has an *italic* word"
    set_text(message, text)
    append_style(message, make_style('ITALIC', 20, 6))

    apply_styles(message)

    assert expected == message.text


async def test_strike_style(message):
    text = "this message has a strikethrough word"
    expected = "this message has a ~strikethrough~ word"
    set_text(message, text)
    append_style(message, make_style('STRIKETHROUGH', 19, 13))

    apply_styles(message)

    assert expected == message.text


async def test_spoiler_style(message):
    text = "this message has a spoiler word"
    expected = "this message has a ||spoiler|| word"
    set_text(message, text)
    append_style(message, make_style('SPOILER', 19, 7))

    apply_styles(message)

    assert expected == message.text


async def test_monospaced_style(message):
    text = "this message has a monospaced word"
    expected = "this message has a `monospaced` word"
    set_text(message, text)
    append_style(message, make_style('MONOSPACE', 19, 10))

    apply_styles(message)

    assert expected == message.text


async def test_unknown_style(message):
    append_style(message, make_style('WONKA', 19, 4))

    try:
        apply_styles(message)
    except UnknownStyle as e:
        assert str(e) == 'Unrecognized style WONKA'


async def test_multi_region(message):
    text = "this message has a bold and an italic word"
    expected = "this message has a **bold** and an *italic* word"
    set_text(message, text)
    append_style(message, make_style('BOLD', 19, 4))
    append_style(message, make_style('ITALIC', 31, 6))

    apply_styles(message)

    assert expected == message.text


async def test_overlap_region(message):
    text = "this message has a bold and an italic word"
    expected = "this message has a **bold** and an *italic* word"
    set_text(message, text)
    append_style(message, make_style('BOLD', 19, 10))
    append_style(message, make_style('ITALIC', 21, 6))

    try:
        apply_styles(message)
    except OverlappingStyleRegions:
        pass


async def test_zero_start_region(message):
    text = "this message has a bold word"
    expected = "**this** message has a bold word"
    set_text(message, text)
    append_style(message, make_style('BOLD', 0, 4))

    apply_styles(message)

    assert expected == message.text


async def test_end_region(message):
    text = "this message has a bold word"
    expected = "this message has a bold **word**"
    set_text(message, text)
    append_style(message, make_style('BOLD', 24, 4))

    apply_styles(message)

    assert expected == message.text


async def test_out_of_bounds_region_end(message):
    text = "ignore style off the end"
    expected = "ignore style off the end"
    set_text(message, text)
    append_style(message, make_style('BOLD', 25, 8))

    apply_styles(message)

    assert expected == message.text


async def test_negative_start_region(message):
    text = "ignore style off the end"
    expected = "ignore style off the end"
    set_text(message, text)
    append_style(message, make_style('BOLD', -1, 8))

    apply_styles(message)

    assert expected == message.text
