from concurrent import futures

import grpc
from api import api_pb2_grpc as api
from api import api_pb2 as dto


class MetaServicer(api.MetaServicer):
	def Echo(self, request, context):
		return dto.EchoRespone(message=request.message)

def main():
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
	api.add_MetaServicer_to_server(MetaServicer(), server)
	server.add_insecure_port("[::]:50051")
	server.start()
	server.wait_for_termination()

if __name__ == "__main__":
	main()