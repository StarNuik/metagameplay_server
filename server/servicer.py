from dependency_injector import providers
from logging import Logger
import injector
from opentelemetry.sdk.trace import Span
from opentelemetry.instrumentation.grpc._server import _OpenTelemetryServicerContext as ServicerContext
from api import api_pb2 as dto
from api import api_pb2_grpc as api

from server import *
from server import jwt_session as jwts

GET_USER_TRACE_NAME = "get_user"

class Servicer:
	pass

def bind_servicer(binder: injector.Binder):
	binder.bind(Servicer, to = Servicer, scope = injector.singleton)

class Servicer(api.AuthServicer, api.ShopServicer):
	@injector.inject
	def __init__(self,
		db_session_factory: DbSessionFactory,
		tracer_span_factory: TracerSpanFactory,
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
			with self.span(GET_USER_TRACE_NAME):
				return self.shop.get_user(db, user_session)

	def GetShopItems(self, _, __):
		with self.db_session() as db:
			return self.shop.get_shop_items(db)
	
	def BuyItem(self, req: dto.BuyItemReq, context: ServicerContext):
		with self.db_session() as db, db.begin():
			user_session = jwts.from_context(context)
			self.shop.buy_item(db, req, user_session)

			with self.span(GET_USER_TRACE_NAME):
				return self.shop.get_user(db, user_session)

	def SellItem(self, req: dto.SellItemReq, context: ServicerContext):
		with self.db_session() as db, db.begin():
			user_session = jwts.from_context(context)
			self.shop.sell_item(db, req, user_session)

			with self.span(GET_USER_TRACE_NAME):
				return self.shop.get_user(db, user_session)