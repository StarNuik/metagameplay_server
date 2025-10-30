from argparse import ArgumentParser
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
	except:
		pass

if __name__ == "__main__":
	main()