import grpc
import logging
from logging import Logger
from injector import Injector

from server import *

def run(injector: Injector):
	log = injector.get(Logger)

	server = injector.get(grpc.Server)
	injector.call_with_injection(migrate_db)

	try:
		server.start()
		server.wait_for_termination()
	except KeyboardInterrupt:
		log.info("Graceful shutdown")
	finally:
		log.info("Waiting for the server to finish (Press CTRL+C again to force shutdown)")
		server.stop(5).wait()
		log.info("All finished, exiting")

def main():
	config = Configuration("./config.json")
	
	injector = Injector([
			lambda binder : binder.bind(Configuration, to = config),
			BindInterceptors,
			bind_auth_usecase,
			BindInfra,
			BindDbClient,
			BindDbSession,
			bind_servicer,
			bind_shop_usecase,
			bind_grpc_server,
		],
		auto_bind = False
	)

	run(injector)

if __name__ == "__main__":
	main()