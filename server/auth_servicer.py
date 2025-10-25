from api import api_pb2 as dto
from api import api_pb2_grpc as api

import jwt

from . import AuthUsecase

class AuthServicer(api.AuthServicer):
	def __init__(self, auth_usecase: AuthUsecase):
		self.usecase = auth_usecase
		pass

	def Login(self, req: dto.LoginReq, context):
		token = self.usecase.login(req.username)
		return dto.UserSession(session_token = token)