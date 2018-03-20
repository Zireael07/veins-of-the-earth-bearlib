# very simple event code based on zope.events
subscribers = []

def notify(event):
    for subscriber in subscribers:
        subscriber(event)