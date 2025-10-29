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

class Servicer(api.AuthServicer, api.ShopServicer):
	def __init__(self,
		logger: Logger,
		db_session_factory: providers.Callable[DbSession],
		tracer_span_factory: providers.Callable[Span],
		auth_usecase: AuthUsecase,
		shop_usecase: ShopUsecase,
	):
		self.db_session = db_session_factory
		self.span = tracer_span_factory
		self.auth = auth_usecase
		self.shop = shop_usecase

	def Login(self, req: dto.LoginReq, __):
		with self.db_session() as db, db.begin():
			user_session = self.auth.login(db, req)
			jwt = jwts.pack(user_session)
			return dto.UserSession(session_token = jwt)

	def GetLoginReward(self, _, context):
		with self.db_session() as db, db.begin():
			user_session = jwts.from_context(context)
			self.shop.receive_login_reward(db, user_session)
			with self.span("get_user"):
				return self.shop.get_user(db, user_session)

	def GetShopItems(self, _, __):
		with self.db_session() as db:
			return self.shop.get_shop_items(db)
	
	def BuyItem(self, req: dto.BuyItemReq, context: ServicerContext):
		with self.db_session() as db, db.begin():
			user_session = jwts.from_context(context)
			self.shop.buy_item(db, req, user_session)

			with self.span("get_user"):
				return self.shop.get_user(db, user_session)

	def SellItem(self, req: dto.SellItemReq, context: ServicerContext):
		with self.db_session() as db, db.begin():
			user_session = jwts.from_context(context)
			self.shop.sell_item(db, req, user_session)

			with self.span("get_user"):
				return self.shop.get_user(db, user_session)