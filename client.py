import argparse
import collections
import logging
from logging import Logger
from typing import Any
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

class ClientBase:
	def __init__(self, logger: Logger):
		self.log = logger

	def log_grpc(self, call, req, caller) -> Any:
		class_name = __class__.__name__
		caller_name = caller.__name__

		self.log.info(f"{class_name}.{caller_name} request:\n{req}")

		resp = call(req)

		self.log.info(f"{class_name}.{caller_name} response:\n{resp}")

		return resp

class AuthClient(ClientBase):
	def __init__(self,
		auth_api: api.AuthStub,
		logger: Logger,
	):
		super().__init__(logger)
		self.auth = auth_api
	
	def Login(self, req: dto.LoginReq) -> dto.UserSession:
		return self.log_grpc(
			self.auth.Login, req, self.Login,
		)
	
class ShopClient(ClientBase):
	def __init__(self,
		shop_api: api.ShopStub,
		logger: Logger,
	):
		super().__init__(logger)
		self.shop = shop_api
	
	def GetLoginReward(self) -> dto.User:
		return self.log_grpc(
			self.shop.GetLoginReward, dto.Empty(), self.GetLoginReward,
		)

	def GetUserData(self) -> dto.User:
		return self.log_grpc(
			self.shop.GetUserData, dto.Empty(), self.GetUserData,
		)
	
	def GetShopItems(self) -> dto.ItemsList:
		return self.log_grpc(
			self.shop.GetShopItems, dto.Empty(), self.GetShopItems,
		)
	
	def BuyItem(self, req: dto.BuyItemReq) -> dto.User:
		return self.log_grpc(
			self.shop.BuyItem, req, self.BuyItem,
		)
	
	def SellItem(self, req: dto.SellItemReq) -> dto.User:
		return self.log_grpc(
			self.shop.SellItem, req, self.SellItem,
		)


class ClientUsecase:
	def __init__(self,
		logger: Logger,
		shop_client: ShopClient,
		auth_client: AuthClient,
		session_repo: SessionRepo,
	):
		self.log = logger
		self.auth = auth_client
		self.shop = shop_client
		self.session = session_repo
	
	def login(self, args):
		req = dto.LoginReq(username = args.username)
		
		resp: dto.UserSession = self.auth.Login(req)

		self.session.set_token(resp.session_token)

		resp = self.shop.GetLoginReward()

	def logout(self, _):
		self.session.delete_token()

	def get_shop_items(self, _):
		resp: dto.ItemsList = self.shop.GetShopItems()

	def buy_item(self, args):
		req = dto.BuyItemReq(item_name = args.item_name)
		resp: dto.User = self.shop.BuyItem(req)

	def sell_item(self, args):
		req = dto.SellItemReq(item_name = args.item_name)
		resp: dto.User = self.shop.SellItem(req)

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
	shop_api = providers.Singleton(
		api.ShopStub,
		grpc_authorized_channel,
	)

	# business
	auth_client = providers.Singleton(
		AuthClient,
		auth_api = auth_api,
		logger = logger,
	)
	shop_client = providers.Singleton(
		ShopClient,
		shop_api = shop_api,
		logger = logger,
	)
	usecase = providers.Singleton(
		ClientUsecase,
		logger = logger,
		shop_client = shop_client,
		auth_client = auth_client,
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

	# Auth
	register = subparsers.add_parser(
		name = "login",
		help = "use credentials to login",
	)
	register.set_defaults(func = usecase.login)
	register.add_argument("username")

	register = subparsers.add_parser(
		name = "logout",
		help = "forget the current user",
	)
	register.set_defaults(func = usecase.logout)

	# Shop
	register = subparsers.add_parser(
		name = "shop_items",
		help = "list all items in shop",
	)
	register.set_defaults(func = usecase.get_shop_items)

	register = subparsers.add_parser(
		name = "buy",
		help = "use credits to buy an item",
	)
	register.set_defaults(func = usecase.buy_item)
	register.add_argument("item_name")

	register = subparsers.add_parser(
		name = "sell",
		help = "sell an item to receive back spent credits",
	)
	register.set_defaults(func = usecase.sell_item)
	register.add_argument("item_name")
	
	return parser

@inject
def error_handling(call, log: Logger = Provide[Container.logger]):
	try:
		call()
	except grpc.RpcError as e:
		log.info(f" grpc error: {e.code().value[1], e.details()}")
	pass

def main():
	logging.basicConfig(
		level=logging.INFO,
	)
	container = Container()
	container.init_resources()
	container.wire(modules=[__name__])

	parser = create_parser()
	args = parser.parse_args()

	error_handling(lambda : args.func(args))

	container.shutdown_resources()

if __name__ == "__main__":
	main()