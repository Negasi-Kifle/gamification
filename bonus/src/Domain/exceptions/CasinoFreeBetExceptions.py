class FreebetError(Exception):
    """Base exception for freebet business errors"""
    pass

class InsufficientFreebetsError(FreebetError):
    """Not enough freebets"""
    pass

class FreebetExpiredError(FreebetError):
    """Freebet has expired"""
    pass

class InvalidFreebetStateError(FreebetError):
    """Invalid state transition"""
    pass