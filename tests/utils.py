from unittest.mock import call

from signalbot import SendMessage

def assert_sent_once(vector, receiver=None, text=None, mentions=None, attachments=None):
    if receiver:
        vector.send.assert_called_once_with(SendMessage(text=text, text_mode='styled', mentions=mentions, attachments=attachments, recipient=receiver))
    else:
        vector.send.assert_called_once_with(SendMessage(text=text, text_mode='styled', mentions=mentions, attachments=attachments))

def assert_sent_multiple(vector, arglists):
    calls = []
    for arglist in arglists:
        calls.append(call(*arglist, text_mode='styled', mentions=None, base64_attachments=None))
    vector.send.assert_has_calls(calls)
