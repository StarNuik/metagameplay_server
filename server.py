from json import JSONEncoder
from pathlib import Path
import random
import grpc
import threading
import logging
import signal
from concurrent import futures
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from logging import Logger


from api import api_pb2 as dto
from api import api_pb2_grpc as api
from server import *
from server import jwt_session as jwts

class AuthInterceptor(grpc.ServerInterceptor):
	def __init__(self):
		def abort(_, context):
			context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")

		self.abort_handler = grpc.unary_unary_rpc_method_handler(abort)

	def intercept_service(self, continuation, handler_call_details):
		path = Path(handler_call_details.method)
		if path.parts[1] == "Auth":
			return continuation(handler_call_details)

		session = jwts.from_details(handler_call_details)
		if session == None:
			return self.abort_handler
		
		resp = continuation(handler_call_details)
		
		return resp

class LoggingInterceptor(grpc.ServerInterceptor):
	def __init__(self, logger: Logger):
		self.log = logger
	
	def intercept_service(self, continuation, handler_call_details):
		resp = continuation(handler_call_details)

		msg = "success" if resp != None else "fail"
		self.log.info(f"{msg} {handler_call_details.method}")
		
		return resp

class Servicer(api.AuthServicer, api.MetaServicer):
	def __init__(self,
		logger: Logger,
		model: Model,
		reward_amount_factory: providers.Callable[int],
	):
		self.log = logger
		self.model = model
		self.reward_amount = reward_amount_factory

	def Login(self, req: dto.LoginReq, context):
		if not self.model.user_exists(req.username):
			self.model.create_user(req.username)
		session = jwts.Session(req.username)
		jwt = jwts.pack(session)
		return dto.UserSession(session_token = jwt)

	def Login2(self, _, context):
		session = jwts.from_context(context)
		username = session.username
		reward = self.reward_amount()
		self.model.add_credits(username, reward)
		return self.GetUserData(_, context)

	def GetUserData(self, _, context):
		session = jwts.from_context(context)
		username = session.username
		user = self.model.get_user(username)
		user = dto.UserData(
			username = username,
			credits = user.balance,
			items = [],
		)
		return user

	def GetShopItems(self, _, context):
		items = self.model.get_all_items()
		resp = dto.ItemsList(items = map(
			lambda item : dto.Item(
				name = item.name,
				price = item.price
			), items))
		return resp

SQLITE_PATH = "./.server.db"

def connect_database() -> Engine:
	engine = create_engine(f"sqlite:///{SQLITE_PATH}")
	install_model(engine)
	return engine

def items_from_config(items) -> list[Item]:
	return map(lambda item : Item(
				name = item["name"],
				price = item["price"],
	), items)

class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

	# infra
	logger = providers.Singleton(
		logging.getLogger,
	)

	# grpc
	logging_interceptor = providers.Singleton(
		LoggingInterceptor,
		logger = logger,
	)

	# Database
	item_list_factory = providers.Factory(
		items_from_config,
		config.data.items,
	)
	database_client = providers.Singleton(
		connect_database,
	)
	session_factory = providers.Factory(
		Session,
		database_client,
	)
	model = providers.Singleton(
		Model,
		session_factory = session_factory.provider,
		item_list_factory = item_list_factory.provider,
	)

	# business
	reward_amount_factory = providers.Factory(
		random.randrange,
		start = config.data.credits_reward.min,
		stop = config.data.credits_reward.max,
	)
	servicer = providers.Singleton(
		Servicer,
		logger = logger,
		model = model,
		reward_amount_factory = reward_amount_factory.provider,
	)

def run(container: Container):
	log = container.logger()

	server = grpc.server(
		futures.ThreadPoolExecutor(max_workers = container.config.server.workers()),
		interceptors = [
			container.logging_interceptor(),
			AuthInterceptor(),
		],
	)
	server.add_insecure_port(f"[::]:{container.config.server.port()}")
	
	api.add_MetaServicer_to_server(container.servicer(), server)
	api.add_AuthServicer_to_server(container.servicer(), server)

	try:
		server.start()
		server.wait_for_termination()
	except KeyboardInterrupt:
		log.info("Graceful shutdown")
	finally:
		log.info("Waiting for the server to finish")
		server.stop(5).wait()
		log.info("All finished, exiting")

def main():
	logging.basicConfig(
		level=logging.INFO,
	)

	container = Container()
	container.init_resources()
	container.wire(modules=[__name__])

	run(container)

	container.shutdown_resources()

if __name__ == "__main__":
	main()