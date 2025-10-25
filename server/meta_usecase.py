from api import api_pb2 as dto
from api import api_pb2_grpc as api

from server import MetaDatabase

class MetaUsecase():
	def __init__(self, db: MetaDatabase):
		self.db = db

	def get_all_items(self):
		return self.db.get_all_items()