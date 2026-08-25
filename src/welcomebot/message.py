from collections import Counter
from pathlib import Path
import re

from signalbot import SendMessage

UUID_RE = r'@[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'

class Attachment:
    def __init__(self, filename, dir=None, data=None):
        self.data = data
        self.dir = dir
        self.filename = Path(filename)


    def __eq__(self, other):
        if isinstance(other, Attachment):
            return (str(self.filename) == str(other.filename) and
                    self.data == other.data)
        return NotImplemented
    
    
    def __hash__(self):
        return hash((self.filename, self.data))


class Message:
    def __init__(self, text, attachments=[], has_attachments=False):
        self.text = text
        self.send_text = ''
        self.attachments = attachments
        self.mentions = None
        self.has_attachments = len(attachments) > 0 if attachments else has_attachments
        self.extract_mentions()


    def __str__(self):
        return f'{self.text}\n[with {len(self.attachments)} attachments]'


    def __eq__(self, other):
        if isinstance(other, Message):
            return (self.text == other.text and
                    Counter(self.attachments) == Counter(other.attachments))
        return NotImplemented

    
    def extract_mentions(self):
        mentions = []
        matches = re.finditer(UUID_RE, self.text)
        output = []
        start = 0
        n = 0
        for match in matches:
            output.append(self.text[start:match.start()])
            n += len(self.text[start:match.start()])
            start = match.end()
            mentions.append({
                'start' : n,
                'length' : 1,
                'author' : match.group()[1:], # should be 'uuid' imho
            })
            output.append('\uFFFC')
            n += 1
        output.append(self.text[start:])
        self.send_text = ''.join(output)
        if mentions:
            self.mentions = mentions

    def add_preamble(self, preamble):
        return Message(preamble + self.text, attachments=self.attachments, has_attachments=self.has_attachments)
        
        
    def send(self, vector, receiver=None):
        attachments = [ str(a.dir / a.filename) for a in self.attachments ] if self.attachments else None
        if receiver:
            # send via bot interface to a specific recipient
            return vector.send(
                SendMessage(
                    text=self.send_text, 
                    attachments=attachments,
                    text_mode="styled",
                    mentions=self.mentions),
                recipient=receiver,
            )
        else:
            # reply to a message context
            return vector.send(
                SendMessage(
                    text=self.send_text, 
                    attachments=attachments,
                    text_mode="styled",
                    mentions=self.mentions),
            )
            
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
    if not message.text_styles:
        return
        
    styles = sorted(message.text_styles, key=lambda x: x.start)
    for i in range(1, len(styles)):
        previous_end = styles[i - 1].start + styles[i - 1].length - 1
        if styles[i].start <= previous_end:
            raise OverlappingStyleRegions()
    text = []
    input = message.text
    ptr = 0
    for style in styles:
        if style.style not in DELIMITERS:
            raise UnknownStyle(f'Unrecognized style {style.style}')
        start = style.start
        end = style.start + style.length
        if start >= ptr and start < len(input):
            text.append(input[ptr:start])
            text.append(DELIMITERS[style.style])
            text.append(input[start:end])
            text.append(DELIMITERS[style.style])
        ptr = end

    if not text:
        text = input
    else:
        text.append(input[end:])

    message.text = ''.join(text)
    return