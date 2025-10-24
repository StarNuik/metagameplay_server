import grpc
import argparse

# from api import api_pb2_grpc as api
# from api import api_pb2 as dto

def register_route(args):
	print(f"[register command]\nurl: {args.url}, username: {args.username}")

def login_route(args):
	print(f"[login command]\nurl: {args.url}, username: {args.username}")

def logout_route(args):
	print("[logout command]")

def main():
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(
		title = "subcommands",
		required = True,
	)

	register = subparsers.add_parser(
		name = "register",
		help = "create a new user"
	)
	register.set_defaults(func = register_route)
	register.add_argument("url")
	register.add_argument("username")

	login = subparsers.add_parser(
		name = "login",
		help = "use credentials to login"
	)
	login.set_defaults(func = login_route)
	login.add_argument("url")
	login.add_argument("username")

	logout = subparsers.add_parser(
		name = "logout",
		help = "end the current session"
	)
	logout.set_defaults(func = logout_route)

	args = parser.parse_args()
	print(args)

	args.func(args)

	# with grpc.insecure_channel("localhost:50051") as channel:
	# 	stub = api.MetaStub(channel)

	# 	request = dto.EchoRequest(message="Hello, world!")
	# 	response = stub.Echo(request)
	# 	print(response)

if __name__ == "__main__":
	main()