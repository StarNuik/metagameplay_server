import grpc

from concurrent import futures
from logging import Logger

from api import api_pb2_grpc as api
from server.auth_servicer import AuthServicer
from server.meta_servicer import MetaServicer

class GrpcServer:
	def __init__(self,
			  log: Logger,
			  meta_servicer: MetaServicer,
			  auth_servicer: AuthServicer,
			  port: int,
			  workers: int):
		server = grpc.server(
			futures.ThreadPoolExecutor(max_workers = workers),
			# interceptors=(MeowInterceptor(),),
		)
		server.add_insecure_port(f"[::]:{port}")
		
		api.add_MetaServicer_to_server(meta_servicer, server)
		api.add_AuthServicer_to_server(auth_servicer, server)

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