import json
from collections import Counter

class Attachment:
    def __init__(self, filename, data=None):
        self.data = data
        self.filename = filename


    def __eq__(self, other):
        if isinstance(other, Attachment):
            return (self.filename == other.filename and
                    self.data == other.data)
        return NotImplemented
    
    
    def __hash__(self):
        return hash((self.filename, self.data))


class Message:
    def __init__(self, text, attachments=[], has_attachments=False):
        self.text = text
        self.attachments = attachments
        self.has_attachments = len(attachments) > 0 if attachments else has_attachments


    def __str__(self):
        return f'{self.text}\n[with {len(self.attachments)} attachments]'


    def __eq__(self, other):
        if isinstance(other, Message):
            return (self.text == other.text and
                    Counter(self.attachments) == Counter(other.attachments))
        return NotImplemented
        
        
    def send(self, vector, receiver=None, preamble=""):
        attachment_data = [a.data for a in self.attachments] if self.attachments else None
        if receiver:
            # send via bot interface to a specific recipient
            if attachment_data:
                return vector.send(receiver, preamble + self.text, base64_attachments=attachment_data, text_mode="styled")
            else:
                return vector.send(receiver, preamble + self.text, text_mode="styled")
        else:
            # reply to a message context
            if attachment_data:
                return vector.send(preamble + self.text, base64_attachments=attachment_data, text_mode="styled")
            else:
                return vector.send(preamble + self.text, text_mode="styled")
            
class OverlappingStyleRegions(Exception):
    pass

class UnknownStyle(Exception):
    pass

DELIMITERS = {
    'BOLD' : '**',
    'ITALIC' : '*',
    'STRIKETHROUGH' : '~',
    'SPOILER' : '||',
    'MONOSPACE' : '`',
}

def apply_styles(message):
    raw = json.loads(message.raw_message)
    if not 'textStyles' in raw['envelope']['dataMessage']:
        return
        
    styles = sorted(raw['envelope']['dataMessage']['textStyles'], key=lambda x: x['start'])
    for i in range(1, len(styles)):
        previous_end = styles[i - 1]['start'] + styles[i - 1]['length'] - 1
        if styles[i]['start'] <= previous_end:
            raise OverlappingStyleRegions()
    text = []
    input = raw['envelope']['dataMessage']['message']
    ptr = 0
    for style in styles:
        if style['style'] not in DELIMITERS:
            raise UnknownStyle(f'Unrecognized style {style['style']}')
        start = style['start']
        end = style['start'] + style['length']
        if start >= ptr and start < len(input):
            text.append(input[ptr:start])
            text.append(DELIMITERS[style['style']])
            text.append(input[start:end])
            text.append(DELIMITERS[style['style']])
        ptr = end

    if not text:
        text = input
    else:
        text.append(input[end:])

    message.text = ''.join(text)
    return