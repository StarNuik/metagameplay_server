from api import api_pb2 as dto
from api import api_pb2_grpc as api

class AuthServicer(api.AuthServicer):
	def __init__(self):
		pass

	def Login(self, request: dto.LoginReq, context):
		return dto.UserSession(session_token = f"{request.username}")