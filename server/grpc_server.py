from json import JSONEncoder
from pathlib import Path
import random
import grpc
import threading
import logging
import signal
from concurrent import futures
import injector
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
from .db_model import _Table

def bind_grpc_server(binder: injector.Binder):
	binder.bind(
		grpc.Server,
		to = injector.CallableProvider(create_grpc_server),
		scope = injector.singleton,
	)

@injector.inject
def create_grpc_server(
	interceptors: list[grpc.ServerInterceptor],
	servicer: Servicer,
	config: Configuration,
):
	server = grpc.server(
		futures.ThreadPoolExecutor(
			max_workers = config.grpc_workers()
		),
		interceptors = interceptors,
	)
	server.add_insecure_port(f"[::]:{config.port()}")
	
	api.add_ShopServicer_to_server(servicer, server)
	api.add_AuthServicer_to_server(servicer, server)
	return server
