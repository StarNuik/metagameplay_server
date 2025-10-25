from client import SessionStorage
from api import api_pb2_grpc as api
from api import api_pb2 as dto
import grpc
from google.protobuf.empty_pb2 import Empty

class MetaUsecase:
	def __init__(self, meta_api: api.MetaStub):
		self.api = meta_api

	def get_inventory(self, args):
		pass
	def get_shop(self, args):
		items = self.api.GetShopItems(Empty())
		print(items)
		pass
	def buy_item(self, args):
		pass