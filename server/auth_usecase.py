import jwt

class AuthUsecase:
	def __init__(self):
		pass

	def login(self, username: str) -> str:
		payload = {
			"username": username,
		}
		key = "secret"
		token = jwt.encode(payload, key, algorithm = "HS256")
		return token