from logging import Logger
from client import SessionStorage
from api import api_pb2_grpc as api
from api import api_pb2 as dto

class AuthUsecase:
	def __init__(self, session_storage: SessionStorage, auth_api: api.AuthStub, logger: Logger):
		# self.session_storage = session_storage
		self.api = auth_api
		self.log = logger
		pass

	def register(self, args):
		print(f"[AuthService.register()]\nhostname: {args.hostname}, username: {args.username}")
		# self.session_storage.save({"hostname": args.hostname, "username": args.username})

	def login(self, args):
		req = dto.LoginReq(username = args.username)
		resp = self.api.Login(req)
		self.log.info(resp)
		# self.session_storage.save({"hostname": args.hostname, "username": args.username})

	def logout(self, _):
		# print("[AuthService.logout()]")
		self.session_storage.drop()