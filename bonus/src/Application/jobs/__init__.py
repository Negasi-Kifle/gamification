"""
Job handlers for the Bonus module.

Per technical guideline §8:
- Job dispatcher (factory) should be in the Application layer
- Maps job_name to the right use case or callable
- Presentation layer only receives requests and calls the dispatcher

Job Names:
- expiring-freebets-notification: Find and notify about expiring freebets
- cleanup-expired-freebets: Mark expired freebets as EXPIRED
"""

from bonus.src.Application.jobs.dispatcher import (
    BonusJobDispatcher,
    get_bonus_dispatcher,
)

__all__ = [
    "BonusJobDispatcher",
    "get_bonus_dispatcher",
]
