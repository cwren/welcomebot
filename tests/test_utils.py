from unittest.mock import call

def assert_sent_once(vector, receiver=None, text=None, mentions=None, base64_attachments=None):
    if receiver:
        vector.send.assert_called_once_with(receiver, text, text_mode='styled', mentions=mentions, base64_attachments=base64_attachments)
    else:
        vector.send.assert_called_once_with(text, text_mode='styled', mentions=mentions, base64_attachments=base64_attachments)

def assert_sent_multiple(vector, arglists):
    calls = []
    for arglist in arglists:
        calls.append(call(*arglist, text_mode='styled', mentions=None, base64_attachments=None))
    vector.send.assert_has_calls(calls)