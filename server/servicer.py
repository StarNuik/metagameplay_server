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