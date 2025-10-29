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
from sqlalchemy.exc import IntegrityError, OperationalError
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
from grpc import ServerInterceptor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from . import *
from .model import _Table

def migrate_schema(engine: Engine, log: Logger):
	try:
		_Table.metadata.create_all(engine, checkfirst = False)
	except OperationalError as e:
		log.info(f"Could not migrate db schema. Reason: {e._message()}")

def migrate_items(engine: Engine, item_list: list[Item], log: Logger):
	try:
		with Session(engine) as session, session.begin():
			session.add_all(item_list)
			session.commit()
	except IntegrityError as e:
		log.info(f"Could not migrate config items. Reason: {e._message()}")

def create_interceptors(
	tracer: Tracer,
	auth_usecase: AuthUsecase
) -> list[ServerInterceptor]:
	return [
		OpenTelemetryServerInterceptor(tracer),
		ExceptionInterceptor(),
		AuthInterceptor(auth_usecase),
	]


SQLITE_PATH = "./.server.db"

def connect_database(item_list, logger: Logger) -> Engine:
	engine = create_engine(f"sqlite:///{SQLITE_PATH}")

	migrate_schema(engine, logger)
	migrate_items(engine, item_list, logger)

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

def create_grpc_server(interceptors, servicer, port, workers):
	server = grpc.server(
		futures.ThreadPoolExecutor(
			max_workers = workers
		),
		interceptors = interceptors,
	)
	server.add_insecure_port(f"[::]:{port}")
	
	api.add_ShopServicer_to_server(servicer, server)
	api.add_AuthServicer_to_server(servicer, server)
	return server

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

	# Database
	item_list = providers.Factory(
		items_from_config,
		items = config.data.items,
	)
	database_client = providers.Singleton(
		connect_database,
		item_list = item_list,
		logger = logger,
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
	auth_usecase = providers.Singleton(
		AuthUsecase,
	)
	shop_usecase = providers.Singleton(
		ShopUsecase,
		reward_amount_factory = reward_amount_factory.provider,
	)
	servicer = providers.Singleton(
		Servicer,
		logger = logger,
		db_session_factory = db_session.provider,
		tracer_span_factory = tracer_span_factory,
		auth_usecase = auth_usecase,
		shop_usecase = shop_usecase,
	)

	# grpc
	interceptors = providers.Singleton(
		create_interceptors,
		tracer = tracer,
		auth_usecase = auth_usecase,
	)
	grpc_server = providers.Singleton(
		create_grpc_server,
		interceptors = interceptors,
		servicer = servicer,
		port = config.server.port,
		workers = config.server.workers,
	)