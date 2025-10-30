from injector import Binder, inject, singleton

from . import Usecase

def bind_service(binder: Binder):
	binder.bind(Service, Service, singleton)

class Service:
	@inject
	def __init__(
		self,
		usecase: Usecase
	):
		self.usecase = usecase

	# TODO user output
	def login(self, args):
		self.usecase.login(args.username)
	
	def logout(self, args):
		self.usecase.logout()
	
	def shop_items(self, args):
		self.usecase.get_shop_items()

	def buy_item(self, args):
		self.usecase.buy_item(args.item_name)

	def sell_item(self, args):
		self.usecase.sell_item(args.item_name)