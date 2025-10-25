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
	
	def start(self):
		self.server.start()
	
	def wait_for_termination(self):
		self.server.wait_for_termination()
	
	def graceful_run(self):
		try:
			self.server.start()
			self.server.wait_for_termination()
		except KeyboardInterrupt as e:
			self.log.info("Graceful shutdown")
		finally:
			self.log.info("Waiting for the server to finish")
			self.server.stop(5).wait()
			self.log.info("All finished, exiting")


class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

	logger = providers.Singleton(
		logging.getLogger,
		__name__,
	)

	meta_db = providers.Singleton(
		MetaDatabase,
		config.data.items,
	)
	meta_usecase = providers.Singleton(
		MetaUsecase,
		meta_db,
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