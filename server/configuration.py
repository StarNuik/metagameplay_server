import logging
from python_json_config import ConfigBuilder
from server import Item

DEFAULT_PORT = 8080
DEFAULT_WORKERS = 1
DEFAULT_ITEM_LIST = []
DEFAULT_SQLITE_PATH = ":memory:"
DEFAULT_CREDITS_REWARD = (0, 0)
DEFAULT_LOG_LEVEL = logging.ERROR

class Configuration():
	def __init__(self, path):
		builder = ConfigBuilder()
		builder.set_field_access_optional()
		builder.validate_field_type("data.items", list)

		self.config = builder.parse_config(path)
	
	def port(self) -> int:
		val = self.config.server.port
		return val if val is not None else DEFAULT_PORT
	
	def grpc_workers(self) -> int:
		val = self.config.server.grpc_workers
		return val if val is not None else DEFAULT_WORKERS
	
	def item_list(self) -> list[Item]:
		val = self.config.data.shop_items
		items = val if val is not None else DEFAULT_ITEM_LIST
		items = map(
			lambda item : Item(
				name = item["name"],
				price = item["price"]
			),
			items,
		)
		return items
	
	def sqlite_path(self) -> str:
		val = self.config.server.sqlite_path
		return val if val is not None else DEFAULT_SQLITE_PATH
	
	def credits_reward(self) -> tuple[int, int]:
		val = (
			self.config.data.credits_reward.min,
			self.config.data.credits_reward.max,
		)
		if val[0] is not None and val[1] is not None:
			return val
		else:
			return DEFAULT_CREDITS_REWARD
	
	def log_level(self) -> int:
		val = self.config.server.log_level
		try:
			return logging.getLevelNamesMapping()[val]
		except:
			return DEFAULT_LOG_LEVEL