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
		print("Logged in")
	
	def logout(self, _):
		self.usecase.logout()
		print("Logged out")
	
	def shop_items(self, _):
		items = self.usecase.get_shop_items()
		print("Shop items:")
		for item in items.items:
			print(f"{{name: {item.name}, price: {item.price}}}")

	def buy_item(self, args):
		self.usecase.buy_item(args.item_name)
		print("Bought")

	def sell_item(self, args):
		self.usecase.sell_item(args.item_name)
		print("Sold")
	
	def user_info(self, _):
		user = self.usecase.get_user()
		print(f"{{username: {user.username}, credits: {user.credits}}}")

	def owned_items(self, _):
		user = self.usecase.get_user()
		print("Owned items:")
		for item in user.items:
			print(f"{{name: {item.name} x{item.quantity}}}")