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

class ShopUsecase:
	def __init__(
		self,
		reward_amount_factory: providers.Callable[int],
	):
		self.reward_amount = reward_amount_factory
		pass

	def get_user(self, db: DbSession, user_session: jwts.Session) -> dto.User:
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
		
		return dto.User(
			username = username,
			credits = user.balance,
			items = items,
		)
	
	def receive_login_reward(self, db: DbSession, user_session: jwts.Session):
		reward = self.reward_amount()
		db.add_credits(user_session.username, reward)
	
	def get_shop_items(self, db: DbSession):
		items = db.get_all_items()
		items = dto.ItemsList(
			items = map(
				lambda item : dto.Item(
					name = item.name,
					price = item.price
				), items
			)
		)
		return items

	def buy_item(self, db: DbSession, req: dto.BuyItemReq, user_session: jwts.Session):
		if not req.item_name:
			raise exc.InvalidArgumentError("item name is empty")
		
		item = db.get_item(req.item_name)
		if item is None:
			raise exc.InvalidArgumentError("item doesn't exist")
	
		user = db.get_user(user_session.username)
		if item.price > user.balance:
			raise exc.FailedPreconditionError("not enough credits")
	
		ownership = db.get_item_ownership(user.username, item.name)
		if ownership is None:
			ownership = db.create_item_ownership(user.username, item.name)

		db.add_credits(user.username, -item.price)
		db.add_to_item_ownership(ownership.id, 1)
	
	def sell_item(self, db: DbSession, req: dto.SellItemReq, user_session: jwts.Session):
		if not req.item_name:
			raise exc.InvalidArgumentError("item name is empty")

		username = user_session.username

		ownership = db.get_item_ownership(username, req.item_name)
		if ownership is None or ownership.quantity <= 0:
			raise exc.FailedPreconditionError("nothing to sell")

		item = db.get_item(req.item_name)
		
		db.add_credits(username, item.price)
		db.add_to_item_ownership(ownership.id, -1)
	
	
