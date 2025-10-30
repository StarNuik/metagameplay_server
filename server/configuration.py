import injector

def bind_configuration(binder: injector.Binder):
	binder.bind(Configuration, Configuration, scope = injector.singleton)

class Configuration:
	port = 65432
	workers = 2
	item_list = []
	sqlite_path = ".server.db"
	reward = {
		"min": 10,
		"max": 100,
	}