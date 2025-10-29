from grpc import StatusCode

UNAUTHENTICATED_MESSAGE = "invalid session token"

# Base
class UsecaseError(Exception):
	def __init__(self, message: str):
		self.message = message
		self.code = StatusCode.UNKNOWN
		super().__init__(message)

# Grpc specific
class InvalidArgumentError(UsecaseError):
	def __init__(self, message: str):
		super().__init__(message)
		self.code = StatusCode.INVALID_ARGUMENT

class FailedPreconditionError(UsecaseError):
	def __init__(self, message: str):
		super().__init__(message)
		self.code = StatusCode.FAILED_PRECONDITION

class UnauthenticatedError(UsecaseError):
	def __init__(self, message: str):
		super().__init__(message)
		self.code = StatusCode.UNAUTHENTICATED

# Unauthenticated
class InvalidSessionError(UnauthenticatedError):
	def __init__(self):
		super().__init__("user session is invalid")

# InvalidArgument
class EmptyUsernameError(InvalidArgumentError):
	def __init__(self):
		super().__init__("username is empty")

class EmptyItemNameError(InvalidArgumentError):
	def __init__(self):
		super().__init__("item name is empty")

class InvalidItemError(InvalidArgumentError):
	def __init__(self):
		super().__init__("item doesn't exist")

# FailedPrecondition
class NotEnoughCreditsError(FailedPreconditionError):
	def __init__(self):
		super().__init__("not enough credits")

class NotEnoughItemsError(FailedPreconditionError):
	def __init__(self):
		super().__init__("no items to sell")