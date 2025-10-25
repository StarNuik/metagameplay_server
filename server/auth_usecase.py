from logging import Logger
import jwt

from . import AuthRepository

JWT_SECRET = "meow"
JWT_ALGO = "HS256"

def pack_user(username: str) -> str:
	payload = {
		"username": username,
	}
	token = jwt.encode(payload, JWT_SECRET, algorithm = JWT_ALGO)
	return token

def unpack_user(token: str) -> str:
	payload = jwt.decode(token, JWT_SECRET, algorithms = [JWT_ALGO])
	return payload["username"]

class AuthUsecase:
	def __init__(self, auth_repository: AuthRepository, logger: Logger):
		self.repo = auth_repository
		self.log = logger

	def login(self, username: str) -> str:
		if not self.repo.user_exists(username):
			self.repo.create_user(username)
			self.log.info(f"user created {{{username}}}")
		
		token = pack_user(username)
		return token
	
	