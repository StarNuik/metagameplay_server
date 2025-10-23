import grpc

from api import api_pb2_grpc as api
from api import api_pb2 as dto

def main():
	with grpc.insecure_channel("localhost:50051") as channel:
		stub = api.MetaStub(channel)

		request = dto.EchoRequest(message="Hello, world!")
		response = stub.Echo(request)
		print(response)

if __name__ == "__main__":
	main()