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

from server import *
from server import jwt_session as jwts
from server import exc
from sqlalchemy.exc import IntegrityError

class AuthUsecase:
	def __init__(self):
		pass
	
	def Login(self, db: DbSession, username: str | None) -> jwts.Session:
		if username is None:
			raise exc.InvalidArgumentError("username is empty")

		if not db.user_exists(username):
			db.create_user(username)
		
		user_session = jwts.Session(username)
		return user_session

	def IsProtectedMethod(self, method: str) -> bool:
		path = Path(method)
		return not path.parts[1] == "Auth"
	
	def IsValidSession(self, user_session: jwts.Session):
		return user_session is not None