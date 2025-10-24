import grpc
import argparse

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

# from api import api_pb2_grpc as api
from api import api_pb2 as dto

from client import *

class AuthService:
	def __init__(self, session_storage: SessionStorage):
		self.session_storage = session_storage
		pass

	def register(self, args):
		print(f"[AuthService.register()]\nurl: {args.url}, username: {args.username}")
		self.session_storage.save({"url": args.url, "username": args.username})

	def login(self, args):
		print(f"[AuthService.login()]\nurl: {args.url}, username: {args.username}")
		self.session_storage.save({"url": args.url, "username": args.username})

	def logout(self, _):
		print("[AuthService.logout()]")
		self.session_storage.drop()

class Container(containers.DeclarativeContainer):
	session_storage = providers.Factory(
		StubSessionStorage,
	)
	auth_service = providers.Factory(
		AuthService,
		session_storage = session_storage,
	)

@inject
def create_parser(
	auth: AuthService = Provide[Container.auth_service],
) -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(
		title = "subcommands",
		required = True,
	)

	register = subparsers.add_parser(
		name = "register",
		help = "create a new user"
	)
	register.set_defaults(func = auth.register)
	register.add_argument("url")
	register.add_argument("username")

	login = subparsers.add_parser(
		name = "login",
		help = "use credentials to login"
	)
	login.set_defaults(func = auth.login)
	login.add_argument("url")
	login.add_argument("username")

	logout = subparsers.add_parser(
		name = "logout",
		help = "end the current session"
	)
	logout.set_defaults(func = auth.logout)
	return parser

def main():
	container = Container()
	container.init_resources()
	container.wire(modules=[__name__])

	parser = create_parser()
	args = parser.parse_args()
	args.func(args)

	# with grpc.insecure_channel("localhost:50051") as channel:
	# 	stub = api.MetaStub(channel)

	# 	request = dto.EchoRequest(message="Hello, world!")
	# 	response = stub.Echo(request)
	# 	print(response)

if __name__ == "__main__":
	main()