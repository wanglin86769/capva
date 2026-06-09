"""Opaque handle for PV monitor subscriptions.

MonitorHandle stores two values returned from provider ``monitor()`` calls:

- owner: the CAPV or PVAPV instance that created this subscription
- handle: CA callback index (int) or p4p Subscription, depending on protocol
"""


class MonitorHandle:
    def __init__(self, owner, handle):
        self._owner = owner
        self._handle = handle
