from api import api_pb2 as dto
from api import api_pb2_grpc as api

from server import MetaRepository

class MetaUsecase():
	def __init__(self, db: MetaRepository):
		self.db = db

	def get_shop_items(self):
		return self.db.get_all_items()