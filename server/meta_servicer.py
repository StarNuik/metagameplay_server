from api import api_pb2 as dto
from api import api_pb2_grpc as api

from server import MetaUsecase

class MetaServicer(api.MetaServicer):
	def __init__(self, usecase: MetaUsecase):
		self.usecase = usecase

	def GetShopItems(self, _, context):
		items = self.usecase.get_all_items()
		return dto.ItemsList(items = map(lambda item : dto.Item(
			id = item.id,
			price = item.price,
			name = item.name
		), items))