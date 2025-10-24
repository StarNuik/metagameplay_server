from concurrent import futures

import grpc
from api import api_pb2_grpc as api
from api import api_pb2 as dto

import logging


class MetaServicer(api.MetaServicer):
	def Echo(self, request, context):
		return dto.EchoRespone(message=request.message)

class MeowInterceptor(grpc.ServerInterceptor):
	def intercept_service(self, continuation, handler_call_details):
		logger = logging.getLogger(__name__)
		logger.info(handler_call_details)
		return continuation(handler_call_details)

def main():
	logging.basicConfig(
		level=logging.INFO,
	)

	server = grpc.server(
		futures.ThreadPoolExecutor(max_workers=2),
		interceptors=(MeowInterceptor(),),
	)
	server.add_insecure_port("[::]:50051")

	api.add_MetaServicer_to_server(MetaServicer(), server)

	server.start()
	server.wait_for_termination()

if __name__ == "__main__":
	main()