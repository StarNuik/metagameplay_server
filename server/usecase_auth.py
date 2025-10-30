from injector import Binder, ClassProvider, singleton
from pathlib import Path

from server import *
from server import jwt_session as jwts
from server import exc
from api import api_pb2 as dto

def bind_auth_usecase(binder: Binder):
	binder.bind(
		AuthUsecase,
		to = ClassProvider(AuthUsecase),
		scope = singleton
	)

class AuthUsecase:
	def __init__(self):
		pass
	
	def login(self, db: DbSession, req: dto.LoginReq) -> jwts.Session:
		username = req.username
		
		if not username:
			raise exc.EmptyUsernameError()

		if not db.user_exists(username):
			db.create_user(username)
		
		user_session = jwts.Session(username)
		return user_session
	
	def authorization_error(self, method: str, user_session: jwts.Session) -> exc.UsecaseError:
		if not self.is_protected_method(method):
			return None
		
		if not self.is_valid_session(user_session):
			return exc.InvalidSessionError()
		
		return None

	def is_protected_method(self, method: str) -> bool:
		path = Path(method)
		return not path.parts[1] == "Auth"
	
	def is_valid_session(self, user_session: jwts.Session):
		return user_session is not None