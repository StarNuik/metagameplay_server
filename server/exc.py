from grpc import StatusCode

UNAUTHENTICATED_MESSAGE = "invalid session token"

class UsecaseError(Exception):
	def __init__(self, message: str):
		self.message = message
		self.code = StatusCode.UNKNOWN
		super().__init__(message)

class InvalidArgumentError(UsecaseError):
	def __init__(self, message: str):
		super().__init__(message)
		self.code = StatusCode.INVALID_ARGUMENT

class FailedPreconditionError(UsecaseError):
	def __init__(self, message: str):
		super().__init__(message)
		self.code = StatusCode.FAILED_PRECONDITION