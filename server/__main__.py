from concurrent import futures

import grpc
from api import api_pb2_grpc as api

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from server import *

import threading
import logging
import signal
from logging import Logger

# class MeowInterceptor(grpc.ServerInterceptor):
# 	def intercept_service(self, continuation, handler_call_details):
# 		logger = logging.getLogger(__name__)
# 		logger.info(handler_call_details)
# 		return continuation(handler_call_details)




class GrpcServer:
	def __init__(self, log: Logger, meta_servicer: MetaServicer, port: int, workers: int):
		server = grpc.server(
			futures.ThreadPoolExecutor(max_workers = workers),
			# interceptors=(MeowInterceptor(),),
		)
		server.add_insecure_port(f"[::]:{port}")
		api.add_MetaServicer_to_server(meta_servicer, server)

		self.server = server
		self.log = log
	
	def graceful_run(self):
		try:
			self.server.start()
			self.server.wait_for_termination()
		except KeyboardInterrupt:
			self.log.info("Graceful shutdown")
		finally:
			self.log.info("Waiting for the server to finish")
			self.server.stop(5).wait()
			self.log.info("All finished, exiting")

import sqlalchemy

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
		logger,
		meta_servicer,
		config.server.port,
		config.server.workers,
	)

@inject
def run_server(grpc_server: GrpcServer = Provide[Container.grpc_server]):
	grpc_server.start()
	grpc_server.wait_for_termination()

import asyncio
def main():
	logging.basicConfig(
		level=logging.INFO,
	)

	container = Container()
	container.init_resources()
	container.wire(modules=[__name__])

	server = container.grpc_server()

	server.graceful_run()

	container.shutdown_resources()

if __name__ == "__main__":
	main()