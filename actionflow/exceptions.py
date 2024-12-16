class ActionflowException(Exception):
    """
    Base exception class for all exceptions raised by the Actionflow package.

    This exception can be used as a catch-all for errors that occur within the
    Actionflow package, allowing for more specific exception handling if needed.

    Attributes:
        None
    """

    pass


class ActionNotFound(ActionflowException):
    """
    Exception raised when an action is not found in the action flow.

    This exception is typically used to indicate that a requested action
    does not exist or cannot be located within the current context of the
    action flow.

    Attributes:
        None
    """

    pass


class ContextAlreadyInitialized(ActionflowException):
    """
    Exception raised when an attempt is made to initialize the context more than once.

    This exception is intended to prevent re-initialization of the context, which
    could lead to unexpected behavior or errors.

    Attributes:
        message (str): Explanation of the error.
    """

    def __init__(self):
        super().__init__("Context has already been initialized.")
