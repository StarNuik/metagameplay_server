from argparse import ArgumentParser
from injector import Binder, CallableProvider, inject, singleton

from . import Service


def bind_parser(binder: Binder):
	binder.bind(
		ArgumentParser,
		CallableProvider(create_parser),
		singleton,
	)

@inject
def create_parser(service: Service) -> ArgumentParser:
	parser = ArgumentParser()
	subparsers = parser.add_subparsers(
		title = "subcommands",
		required = True,
	)

	# Auth
	login = subparsers.add_parser(
		name = "login",
		help = "use credentials to login",
	)
	login.set_defaults(func = service.login)
	login.add_argument("username")

	logout = subparsers.add_parser(
		name = "logout",
		help = "forget the current user",
	)
	logout.set_defaults(func = service.logout)

	# Shop
	shop_items = subparsers.add_parser(
		name = "shop_items",
		help = "list all items in shop",
	)
	shop_items.set_defaults(func = service.shop_items)

	buy = subparsers.add_parser(
		name = "buy",
		help = "use credits to buy an item",
	)
	buy.set_defaults(func = service.buy_item)
	buy.add_argument("item_name")

	sell = subparsers.add_parser(
		name = "sell",
		help = "sell an item to receive back spent credits",
	)
	sell.set_defaults(func = service.sell_item)
	sell.add_argument("item_name")
	return parser