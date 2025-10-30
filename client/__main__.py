from argparse import ArgumentParser
import grpc
from injector import Injector, singleton

from . import *

def main():
	config = Configuration("./config.json")

	injector = Injector([
			lambda binder : binder.bind(Configuration, config, singleton),
			BindGrpc,
			BindInfra,
			bind_interceptors,
			bind_parser,
			bind_repository,
			bind_service,
			bind_usecase,
		],
		auto_bind = False,
	)

	parser = injector.get(ArgumentParser)
	args = parser.parse_args()

	try:
		args.func(args)
	except exc.UsecaseError as e:
		print(f"Error: {e.message}")
	except grpc.RpcError as e:
		print(f"Error: {e.details()}")
	except Exception as e:
		print(f"Error: {type(e)}")

if __name__ == "__main__":
	main()