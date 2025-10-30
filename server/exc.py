from grpc import StatusCode

UNAUTHENTICATED_MESSAGE = "invalid session token"

# Base
class UsecaseError(Exception):
	message = "unknown server error"
	code = StatusCode.UNKNOWN

# Grpc specific
class InvalidArgumentError(UsecaseError):
	code = StatusCode.INVALID_ARGUMENT

class FailedPreconditionError(UsecaseError):
	code = StatusCode.FAILED_PRECONDITION

class UnauthenticatedError(UsecaseError):
	code = StatusCode.UNAUTHENTICATED

# Unauthenticated
class InvalidSessionError(UnauthenticatedError):
	message = "user session is invalid"

# InvalidArgument
class EmptyUsernameError(InvalidArgumentError):
	message = "username is empty"

class EmptyItemNameError(InvalidArgumentError):
	message = "item name is empty"

class InvalidItemError(InvalidArgumentError):
		message = "item doesn't exist"

# FailedPrecondition
class NotEnoughCreditsError(FailedPreconditionError):
		message = "not enough credits"

class NotEnoughItemsError(FailedPreconditionError):
		message = "no items to sell"