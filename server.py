from json import JSONEncoder
import json
from pathlib import Path
import random
import grpc
import threading
import logging
import signal
import jwt
from concurrent import futures
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from logging import Logger
from sqlalchemy import Text, BigInteger, Integer, ForeignKey, Identity, Column, Engine, create_engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from jwt.exceptions import PyJWTError

from api import api_pb2 as dto
from api import api_pb2_grpc as api

class ModelBase(DeclarativeBase):
	pass

class User(ModelBase):
	__tablename__ = "users"

	username: Mapped[str] = mapped_column(Text, primary_key = True)
	balance: Mapped[int] = mapped_column(Integer, default = 0, nullable = False)

class Item(ModelBase):
	__tablename__ = "items"

	id: Mapped[int] = Column("id", BigInteger, Identity(always = True), primary_key = True)
	name: Mapped[str] = mapped_column(Text, nullable = False)
	price: Mapped[int] = mapped_column(Integer, nullable = False)

	def __str__(self):
		return f"{{id: {self.id}, name: {self.name}, price: {self.price}}}"

JWT_SECRET = "meow"
JWT_ALGO = "HS256"
JWT_PAYLOAD_KEY = "__payload"
JWT_HEADER = "session_token"

class SessionPayload():
	def __init__(self, username):
		self.username = username
	def as_json(self):
		return json.dumps(self, default = lambda obj : obj.__dict__)

def as_payload(jsn: str) -> SessionPayload:
	dct = json.loads(jsn)
	return SessionPayload(dct["username"])

def jwt_pack(payload: SessionPayload) -> str:
	jwt_payload = {
		JWT_PAYLOAD_KEY: payload.as_json(),
	}
	token = jwt.encode(jwt_payload, JWT_SECRET, algorithm = JWT_ALGO)
	return token

def jwt_unpack(token: str) -> SessionPayload | None:
	try:
		jwt_payload = jwt.decode(token, JWT_SECRET, algorithms = [JWT_ALGO])
		payload_string = jwt_payload[JWT_PAYLOAD_KEY]
		payload = as_payload(payload_string)
		return payload
	except PyJWTError:
		return None

def jwt_from_metadata(metadata: dict[str, str | bytes]) -> SessionPayload | None:
	if not JWT_HEADER in metadata:
		return None
	token = metadata[JWT_HEADER]

	payload = jwt_unpack(token)
	return payload

def jwt_from_details(details: grpc.HandlerCallDetails) -> SessionPayload | None:
	metadata = dict(details.invocation_metadata)
	return jwt_from_metadata(metadata)

def jwt_from_context(context: grpc.ServicerContext) -> SessionPayload | None:
	metadata = dict(context.invocation_metadata())
	return jwt_from_metadata(metadata)

class AuthInterceptor(grpc.ServerInterceptor):
	def __init__(self):
		def abort(_, context):
			context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")

		self.abort_handler = grpc.unary_unary_rpc_method_handler(abort)

	def intercept_service(self, continuation, handler_call_details):
		path = Path(handler_call_details.method)
		if path.parts[1] == "Auth":
			return continuation(handler_call_details)
		
		payload = jwt_from_details(handler_call_details)
		if payload == None:
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

class Model:
	def __init__(self,
		session_factory: providers.Callable[Session]
	):
		self.session = session_factory

	# Read
	def user_exists(self, username: str) -> bool:
		with self.session() as session:
			stmt = select(User).where(User.username == username)
			return session.scalars(stmt).first() != None
	
	def get_user(self, username: str) -> User:
		with self.session() as session:
			stmt = select(User).where(User.username == username)
			return session.scalars(stmt).one()

	# Update
	def create_user(self, username: str):
		with self.session() as session:
			session.add(User(username = username))
			session.commit()
		
	def add_credits(self, username: str, amount: int):
		with self.session() as session:
			stmt = update(User) \
				.where(User.username == username) \
				.values(balance = User.balance + amount)
			session.execute(stmt)
			session.commit()

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
		payload = SessionPayload(req.username)
		token = jwt_pack(payload)
		return dto.UserSession(session_token = token)

	def Login2(self, _, context):
		payload = jwt_from_context(context)
		username = payload.username
		reward = self.reward_amount()
		self.model.add_credits(username, reward)
		return self.GetUserData(_, context)

	def GetUserData(self, _, context):
		payload = jwt_from_context(context)
		username = payload.username
		user = self.model.get_user(username)
		return dto.UserData(username = username, credits = user.balance, items = [],)

def connect_database() -> Engine:
	engine = create_engine("sqlite:///db.sqlite3")
	ModelBase.metadata.create_all(engine)
	return engine

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

# def create_engine() -> sqlalchemy.Engine:
# 	engine = sqlalchemy.create_engine("sqlite:///db.sqlite3")
# 	install_model(engine)
# 	return engine



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