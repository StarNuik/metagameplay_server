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
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from injector import Injector, Module, provider

from server import *
from server import jwt_session as jwts

def run(injector: Injector):
	log = injector.get(Logger)

	server = injector.get(grpc.Server)
	injector.call_with_injection(migrate_db)

	try:
		server.start()
		server.wait_for_termination()
	except KeyboardInterrupt:
		log.info("Graceful shutdown")
	finally:
		log.info("Waiting for the server to finish (Press CTRL+C again to force shutdown)")
		server.stop(5).wait()
		log.info("All finished, exiting")

def main():
	config = Configuration("./config.json")
	logging.basicConfig(
		level = config.log_level(),
	)


	injector = Injector([
			lambda binder : binder.bind(Configuration, to = config),
			BindInterceptors,
			bind_auth_usecase,
			BindInfra,
			BindDbClient,
			BindDbSession,
			bind_servicer,
			bind_shop_usecase,
			bind_grpc_server,
		],
		auto_bind = False
	)

	run(injector)

if __name__ == "__main__":
	main()