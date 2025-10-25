from pathlib import Path
import grpc
import threading
import logging
import signal
import jwt
from concurrent import futures
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from logging import Logger
from sqlalchemy import Text, BigInteger, Integer, ForeignKey, Identity, Column, Engine, create_engine, select
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

def jwt_pack(username: str) -> str:
	payload = {
		"username": username,
	}
	token = jwt.encode(payload, JWT_SECRET, algorithm = JWT_ALGO)
	return token

def jwt_unpack(token: str) -> str | None:
	try:
		payload = jwt.decode(token, JWT_SECRET, algorithms = [JWT_ALGO])
		return payload["username"]
	except PyJWTError:
		return None

def username_from_metadata(metadata: tuple[tuple[str, str | bytes], ...]) -> str | None:
	metadata = dict(metadata)

	if not "session_token" in metadata:
		return None
	token = metadata["session_token"]

	username = jwt_unpack(token)
	return username

class AuthInterceptor(grpc.ServerInterceptor):
	def __init__(self):
		def abort(_, context):
			context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session token")

		self.abort_handler = grpc.unary_unary_rpc_method_handler(abort)

	def intercept_service(self, continuation, handler_call_details):
		path = Path(handler_call_details.method)
		if path.parts[1] == "Auth":
			return continuation(handler_call_details)
		
		print(dict(handler_call_details.invocation_metadata))

		username = username_from_metadata(handler_call_details.invocation_metadata)
		if username == None:
			return self.abort_handler
		
		resp = continuation(handler_call_details)
		
		return resp

class LoggingInterceptor(grpc.ServerInterceptor):
	def __init__(self, logger: Logger):
		self.log = logger
	
	def intercept_service(self, continuation, handler_call_details):
		handler_call_details.invocation_metadata
		resp = continuation(handler_call_details)

		msg = "success" if resp != None else "fail"
		self.log.info(f"{msg} {handler_call_details.method}")
		
		return resp

class Model:
	def __init__(self, session_factory: providers.Callable[Session]):
		self.session = session_factory
	
	def user_exists(self, username: str) -> bool:
		with self.session() as session:
			stmt = select(User).where(User.username == username)
			return session.scalars(stmt).first() != None
	
	def create_user(self, username: str):
		with self.session() as session:
			session.add(User(username = username))
			session.commit()

class Servicer(api.AuthServicer, api.MetaServicer):
	def __init__(self, logger: Logger, model: Model):
		self.log = logger
		self.model = model

	def Login(self, req: dto.LoginReq, context: grpc.ServicerContext):
		if not self.model.user_exists(req.username):
			self.model.create_user(req.username)
		token = jwt_pack(req.username)
		return dto.UserSession(session_token = token)

	def Login2(self, req: dto.Empty, context):
		return dto.UserData(username = "TODO", credits = -1, items = [],)

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
	servicer = providers.Singleton(
		Servicer,
		logger = logger,
		model = model,
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