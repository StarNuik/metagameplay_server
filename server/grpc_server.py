import grpc
from concurrent import futures
import injector
from api import api_pb2_grpc as api

from . import *

def bind_grpc_server(binder: injector.Binder):
	binder.bind(
		grpc.Server,
		to = injector.CallableProvider(create_grpc_server),
		scope = injector.singleton,
	)

@injector.inject
def create_grpc_server(
	interceptors: list[grpc.ServerInterceptor],
	servicer: Servicer,
	config: Configuration,
):
	server = grpc.server(
		futures.ThreadPoolExecutor(
			max_workers = config.grpc_workers()
		),
		interceptors = interceptors,
	)
	server.add_insecure_port(f"[::]:{config.port()}")
	
	api.add_ShopServicer_to_server(servicer, server)
	api.add_AuthServicer_to_server(servicer, server)
	return server
