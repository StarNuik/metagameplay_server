import sqlalchemy
from dependency_injector import containers, providers
import logging

from server import *

def create_engine() -> sqlalchemy.Engine:
	engine = sqlalchemy.create_engine("sqlite:///db.sqlite3")
	install_model(engine)
	return engine
	

class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

	logger = providers.Singleton(
		logging.getLogger,
		__name__,
	)

	database_client = providers.Singleton(
		create_engine,
	)

	auth_usecase = providers.Singleton(
		AuthUsecase,
	)
	auth_servicer = providers.Singleton(
		AuthServicer,
		auth_usecase = auth_usecase,
	)

	meta_repo = providers.Singleton(
		MetaRepository,
		items = config.data.items,
		database = database_client,
	)
	meta_usecase = providers.Singleton(
		MetaUsecase,
		meta_repo,
	)
	meta_servicer = providers.Singleton(
		MetaServicer,
		meta_usecase,
	)
	
	grpc_server = providers.Singleton(
		GrpcServer,
		log = logger,
		meta_servicer = meta_servicer,
		auth_servicer = auth_servicer,
		port = config.server.port,
		workers = config.server.workers,
	)