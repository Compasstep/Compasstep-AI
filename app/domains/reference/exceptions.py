"""
Custom exceptions for the reference domain.
These exceptions are used in the service layer and handled in the router layer
to return appropriate API responses.
"""

class UserSuspendedError(Exception):
    """Raised when a user is in SUSPENDED or BLOCKED state."""
    pass


class UserNotFoundError(Exception):
    """Raised when the user_id does not exist in the database."""
    pass


class AgentExecutionError(Exception):
    """Raised when the AgentExecutor fails unexpectedly."""
    pass
