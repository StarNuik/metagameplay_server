
UNAUTHENTICATED_MESSAGE = "invalid session token"

class _ErrorBase(Exception):
	pass

class InvalidArgumentError(_ErrorBase):
	def __init__(self, message: str):
		super().__init__(message)