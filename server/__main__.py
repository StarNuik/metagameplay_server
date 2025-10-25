from concurrent import futures

import grpc


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




@inject
def run_server(grpc_server: GrpcServer = Provide[Container.grpc_server]):
	grpc_server.start()
	grpc_server.wait_for_termination()

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