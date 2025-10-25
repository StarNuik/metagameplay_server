from concurrent import futures

import grpc
from api import api_pb2_grpc as api

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from server import *

# import logging

# class MeowInterceptor(grpc.ServerInterceptor):
# 	def intercept_service(self, continuation, handler_call_details):
# 		logger = logging.getLogger(__name__)
# 		logger.info(handler_call_details)
# 		return continuation(handler_call_details)

# def main():


	
# 	logging.basicConfig(
# 		level=logging.INFO,
# 	)

# 	server = grpc.server(
# 		futures.ThreadPoolExecutor(max_workers=2),
# 		# interceptors=(MeowInterceptor(),),
# 	)
# 	server.add_insecure_port("[::]:50051")

# 	api.add_MetaServicer_to_server(MetaUsecase(), server)

# 	server.start()
# 	server.wait_for_termination()

class GrpcServer:
	def __init__(self, meta_servicer: MetaServicer, port: int, workers: int):
		grpc_server = grpc.server(
			futures.ThreadPoolExecutor(max_workers = workers),
			# interceptors=(MeowInterceptor(),),
		)
		grpc_server.add_insecure_port(f"[::]:{port}")
		api.add_MetaServicer_to_server(meta_servicer, grpc_server)

		self.server = grpc_server
	
	def start(self):
		self.server.start()
	
	def wait_for_termination(self):
		self.server.wait_for_termination()

class Container(containers.DeclarativeContainer):
	config = providers.Configuration(json_files = ["./config.json"])

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
		meta_servicer,
		config.server.port,
		config.server.workers,
	)

@inject
def run_server(grpc_server: GrpcServer = Provide[Container.grpc_server]):
	grpc_server.start()
	grpc_server.wait_for_termination()


def main():
	container = Container()
	container.init_resources()
	container.wire(modules=[__name__])

	run_server()

	container.shutdown_resources()

if __name__ == "__main__":
	main()