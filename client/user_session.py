class UserSession:
	def __init__(self, hostname, username, token):
		self.hostname = hostname
		self.username = username
		self.token = token
		pass

	def __eq__(self, other): 
		if not isinstance(other, UserSession):
			return NotImplemented

		return self.hostname == other.hostname and self.username == other.username and self.token == self.token