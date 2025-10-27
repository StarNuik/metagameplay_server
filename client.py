import argparse
import collections
import logging
from logging import Logger
from dependency_injector import providers, containers
from dependency_injector.providers import Callable
from dependency_injector.wiring import inject, Provide
import grpc
from pathlib import Path
from api import api_pb2_grpc as api
from api import api_pb2 as dto

SESSION_FILE_PATH = "./.client.db"

class SessionRepo:
	def __init__(self):
		self.token = None

	def set_token(self, token: str):
		with open(SESSION_FILE_PATH, "w") as file:
			file.write(token)

	def get_token(self) -> str | None:
		path = Path(SESSION_FILE_PATH)
		if not path.exists():
			return None
		
		with open(SESSION_FILE_PATH, "r") as file:
			return file.read()
	
	def delete_token(self):
		path = Path(SESSION_FILE_PATH)
		path.unlink(missing_ok = True)

class ClientUsecase:
	def __init__(self,
		logger: Logger,
		meta_api: api.MetaStub,
		auth_api: api.AuthStub,
		session_repo: SessionRepo,
	):
		self.log = logger
		self.auth = auth_api
		self.meta = meta_api
		self.session = session_repo
	
	def login(self, args):
		req = dto.LoginReq(username = args.username)
		resp: dto.UserSession = self.auth.Login(req)
		self.session.set_token(resp.session_token)
		self.log.info(f"login: {self.session.get_token()}")

		resp = self.meta.Login2(dto.Empty())
		self.log.info(f"user data: {resp}")

	def logout(self, _):
		pass
	def get_shop_items(self, args):
		resp: dto.ItemsList = self.meta.GetShopItems(dto.Empty())
		self.log.info(f"all items: {resp}")
		pass
	def buy_item(self, args):
		pass
	def sell_item(self, args):
		pass

JWT_HEADER_NAME = "session_token"

class ClientCallDetails(
	# collections.namedtuple(
	# 	"ClientCallDetails", ("method", "timeout", "metadata", "credentials")
	# ),
	grpc.ClientCallDetails,
):
	def __init__(self, old: grpc.ClientCallDetails, metadata):
		self.method = old.method
		self.timeout = old.timeout
		self.metadata = metadata
		self.credentials = old.credentials

class AddSessionInterceptor(grpc.UnaryUnaryClientInterceptor):
	def __init__(self, session_repo: SessionRepo):
		self.session_token = session_repo.get_token

	def intercept_unary_unary(self, continuation, client_call_details: grpc.ClientCallDetails, request):
		metadata = []
		if client_call_details.metadata is not None:
			metadata = list(client_call_details.metadata)
		metadata.append((JWT_HEADER_NAME, self.session_token()))
		client_call_details = ClientCallDetails(client_call_details, metadata)
		return continuation(client_call_details, request)

class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

	# infra
	logger = providers.Singleton(
		logging.getLogger,
		__name__,
	)

	# storage
	session_repo = providers.Singleton(
		SessionRepo,
	)

	# grpc
	grpc_channel = providers.Resource(
		grpc.insecure_channel,
		config.client.hostname,
	)
	add_session_interceptor = providers.Singleton(
		AddSessionInterceptor,
		session_repo = session_repo,
	)
	grpc_authorized_channel = providers.Singleton(
		grpc.intercept_channel,
		grpc_channel,
		add_session_interceptor,
	)
	auth_api = providers.Singleton(
		api.AuthStub,
		grpc_channel,
	)
	meta_api = providers.Singleton(
		api.MetaStub,
		grpc_authorized_channel,
	)

	# business
	usecase = providers.Singleton(
		ClientUsecase,
		logger = logger,
		meta_api = meta_api,
		auth_api = auth_api,
		session_repo = session_repo,
	)

@inject
def create_parser(
	usecase: ClientUsecase = Provide[Container.usecase]
) -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(
		title = "subcommands",
		required = True,
	)

	register = subparsers.add_parser(
		name = "login",
		help = "use credentials to login",
	)
	register.set_defaults(func = usecase.login)
	register.add_argument("username")

	register = subparsers.add_parser(
		name = "shop_items",
		help = "list all items in shop",
	)
	register.set_defaults(func = usecase.get_shop_items)
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

	try:
		args.func(args)
	except grpc.RpcError as e:
		container.logger().info(e)

	container.shutdown_resources()

if __name__ == "__main__":
	main()