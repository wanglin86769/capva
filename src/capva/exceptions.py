"""Custom exceptions for capva."""


class EPICSProtocolError(Exception):
    """Raised when protocol detection or selection fails."""
    pass


class EPICSConnectionError(Exception):
    """Raised when connection to PV fails."""
    pass


class EPICSGetError(Exception):
    """Raised when a get operation fails after the PV is reachable."""
    pass


class EPICSPutError(Exception):
    """Raised when a put operation fails after the PV is reachable."""
    pass


class EPICSTimeoutError(Exception):
    """Raised when PV operation times out."""
    pass
