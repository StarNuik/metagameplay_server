class UsecaseError(Exception):
	message = "unknown error"

class LoggedInError(UsecaseError):
	message = "already logged in"

class NotLoggedInError(UsecaseError):
	message = "not logged in"

class LoggedOutError(UsecaseError):
	message = "already logged out"