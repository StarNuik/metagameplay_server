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
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, Span, Tracer
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor
from opentelemetry.instrumentation.grpc._server import _OpenTelemetryServicerContext as ServicerContext
from api import api_pb2 as dto
from api import api_pb2_grpc as api
from server import *
from server import jwt_session as jwts
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

class AuthInterceptor(grpc.ServerInterceptor):
	def __init__(self):
		def abort(_, context: ServicerContext):
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
	def __init__(self, tracer_span_factory: providers.Callable[Span]):
		self.span = tracer_span_factory
	
	def intercept_service(self, continuation, handler_call_details):
		with self.span(name = "meow"):
			resp = continuation(handler_call_details)
			return resp

class Servicer(api.AuthServicer, api.ShopServicer):
	def __init__(self,
		logger: Logger,
		db_session_factory: providers.Callable[DbSession],
		reward_amount_factory: providers.Callable[int],
		tracer_span_factory: providers.Callable[Span],
	):
		self.log = logger
		self.db_session = db_session_factory
		self.reward_amount = reward_amount_factory
		self.span = tracer_span_factory

	# Read
	def __get_user_data(self,
		db: DbSession,
		user_session: jwts.Session
	) -> dto.User:
		with self.span("get_user_data"):
			username = user_session.username
			user = db.get_user(username)
			items = []

			for ownership in db.get_all_ownerships(username):
				if ownership.quantity <= 0:
					continue
				
				items.append(dto.OwnedItem(
					name = ownership.item_name,
					quantity = ownership.quantity,
				))
			
			user = dto.User(
				username = username,
				credits = user.balance,
				items = items,
			)
			return user

	def Login(self, req: dto.LoginReq, context):
		# TODO: empty username / None username
		with self.db_session() as db, db.begin():
			user_session = jwts.Session(req.username)
			if not db.user_exists(req.username):
				db.create_user(req.username)
		
		jwt = jwts.pack(user_session)
		return dto.UserSession(session_token = jwt)

	def GetUserData(self, _, context):
		with self.db_session() as db:
			user_session = jwts.from_context(context)
			return self.__get_user_data(db, user_session)

	def GetShopItems(self, _, context):
		with self.db_session() as db:
			items = db.get_all_items()
			resp = dto.ItemsList(items = map(
				lambda item : dto.Item(
					name = item.name,
					price = item.price
				), items))
			return resp

	# Modify
	def GetLoginReward(self, _, context):
		with self.db_session() as db, db.begin():
			reward = self.reward_amount()
			user_session = jwts.from_context(context)
			username = user_session.username
			db.add_credits(username, reward)
		
			return self.__get_user_data(db, user_session)
	
	def BuyItem(self, req: dto.BuyItemReq, context: ServicerContext):
		with self.db_session() as db, db.begin():
			item = db.get_item(req.item_name)
			if item is None:
				context.abort(grpc.StatusCode.INVALID_ARGUMENT, "item doesn't exist")
				return
		
			user_session = jwts.from_context(context)
			user = db.get_user(user_session.username)
			if item.price > user.balance:
				context.abort(grpc.StatusCode.FAILED_PRECONDITION, "not enough credits")
				return
		
			ownership = db.get_item_ownership(user.username, item.name)
			if ownership is None:
				ownership = db.create_item_ownership(user.username, item.name)

			db.add_to_item_ownership(ownership.id, 1)
			db.add_credits(user.username, -item.price)

			return self.__get_user_data(db, user_session)

	def SellItem(self, req: dto.SellItemReq, context: ServicerContext):
		with self.db_session() as db, db.begin():
			
			user_session = jwts.from_context(context)
			username = user_session.username
			# user = db.get_user(user_session.username)
			ownership = db.get_item_ownership(username, req.item_name)
			if ownership is None or ownership.quantity <= 0:
				context.abort(grpc.StatusCode.FAILED_PRECONDITION, "user doesn't own this item")
				return

			item = db.get_item(req.item_name)
			
			db.add_credits(username, item.price)
			db.add_to_item_ownership(ownership.id, -1)

			return self.__get_user_data(db, user_session)

SQLITE_PATH = "./.server.db"

def connect_database(item_list) -> Engine:
	engine = create_engine(f"sqlite:///{SQLITE_PATH}")
	install_model(engine)
	migrate_items(engine, item_list)
	SQLAlchemyInstrumentor().instrument(
		engine = engine,
	)
	return engine

def items_from_config(items) -> list[Item]:
	return map(lambda item : Item(
				name = item["name"],
				price = item["price"],
	), items)

def connect_tracer() -> Tracer:
	resource = Resource(
		attributes={
			"service.name": "meow",
		}
	)
	provider = TracerProvider(
		resource = resource
	)
	trace.set_tracer_provider(provider)

	exporter = BatchSpanProcessor(OTLPSpanExporter())

	trace.get_tracer_provider().add_span_processor(exporter)

	tracer = trace.get_tracer(__name__)

	return tracer

def get_tracer_span(tracer: Tracer):
	return lambda name : tracer.start_as_current_span(name)
	return tracer.start_as_current_span(name)

class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

	# infra
	logger = providers.Singleton(
		logging.getLogger,
	)
	tracer = providers.Singleton(
		connect_tracer,
	)
	tracer_span_factory = providers.Factory(
		get_tracer_span,
		tracer = tracer,
	)

	# grpc
	otlp_interceptor = providers.Singleton(
		OpenTelemetryServerInterceptor,
		tracer,
	)

	# Database
	item_list = providers.Factory(
		items_from_config,
		config.data.items,
	)
	database_client = providers.Singleton(
		connect_database,
		item_list = item_list,
	)
	session_factory = providers.Factory(
		Session,
		database_client,
	)
	db_session = providers.Factory(
		DbSession,
		session_factory = session_factory.provider,
		tracer_span_factory = tracer_span_factory,
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
		db_session_factory = db_session.provider,
		reward_amount_factory = reward_amount_factory.provider,
		tracer_span_factory = tracer_span_factory,
	)

def run(container: Container):
	log = container.logger()

	server = grpc.server(
		futures.ThreadPoolExecutor(
			max_workers = container.config.server.workers()
		),
		interceptors = [
			container.otlp_interceptor(),
			AuthInterceptor(), # TODO
		],
	)
	server.add_insecure_port(f"[::]:{container.config.server.port()}")
	
	api.add_ShopServicer_to_server(container.servicer(), server)
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