import logging
import grpc
import argparse

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from api import api_pb2_grpc as api
from api import api_pb2 as dto

from client import *

class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

	grpc_channel = providers.Resource(
		grpc.insecure_channel,
		config.client.hostname,
	)

	logger = providers.Singleton(
		logging.getLogger,
		__name__,
	)

	meta_api = providers.Singleton(
		api.MetaStub,
		grpc_channel,
	)
	meta_usecase = providers.Singleton(
		MetaUsecase,
		meta_api,
	)

	# session_storage = providers.Singleton(
	# 	StubSessionStorage,
	# )
	meta_auth = providers.Singleton(
		api.AuthStub,
		grpc_channel,
	)
	auth_usecase = providers.Singleton(
		AuthUsecase,
		session_storage = None,
		auth_api = meta_auth,
		logger = logger,
	)

@inject
def create_parser(
	auth: AuthUsecase = Provide[Container.auth_usecase],
	meta: MetaUsecase = Provide[Container.meta_usecase],
) -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(
		title = "subcommands",
		required = True,
	)

	shop = subparsers.add_parser(
		"shop",
		help = "show all shop items",
	)
	shop.set_defaults(func = meta.get_shop)

	# register = subparsers.add_parser(
	# 	name = "register",
	# 	help = "create a new user",
	# )
	# register.set_defaults(func = auth.register)
	# register.add_argument("hostname")
	# register.add_argument("username")

	login = subparsers.add_parser(
		name = "login",
		help = "use credentials to login"
	)
	login.set_defaults(func = auth.login)
	# login.add_argument("hostname")
	login.add_argument("username")

	# logout = subparsers.add_parser(
	# 	name = "logout",
	# 	help = "end the current session"
	# )
	# logout.set_defaults(func = auth.logout)
	return parser

def main():
	logging.basicConfig(
		level=logging.INFO,
	)
	
	container = Container()
	container.init_resources()
	container.wire(modules=[__name__])

	parser = create_parser()
	args = parser.parse_args()
	args.func(args)

	container.shutdown_resources()

	# with grpc.insecure_channel("localhost:50051") as channel:
	# 	stub = api.MetaStub(channel)

	# 	request = dto.EchoRequest(message="Hello, world!")
	# 	response = stub.Echo(request)
	# 	print(response)

if __name__ == "__main__":
	main()