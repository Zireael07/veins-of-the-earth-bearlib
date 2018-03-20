# very simple event code based on zope.events

class GameEvent():
    def __init__(self, event_type, data):
        self.type = event_type
        self.data = data


subscribers = []

def notify(event):
    for subscriber in subscribers:
        subscriber(event)