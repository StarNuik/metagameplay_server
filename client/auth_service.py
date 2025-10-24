from client import SessionStorage
from api import api_pb2_grpc as api

class AuthService:
	def __init__(self, session_storage: SessionStorage, api_auth: api.AuthStub):
		self.session_storage = session_storage
		pass

	def register(self, args):
		print(f"[AuthService.register()]\nhostname: {args.hostname}, username: {args.username}")
		# self.session_storage.save({"hostname": args.hostname, "username": args.username})

	def login(self, args):
		print(f"[AuthService.login()]\nhostname: {args.hostname}, username: {args.username}")
		# self.session_storage.save({"hostname": args.hostname, "username": args.username})

	def logout(self, _):
		# print("[AuthService.logout()]")
		self.session_storage.drop()