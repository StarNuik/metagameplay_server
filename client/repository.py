from dataclasses import dataclass
from pathlib import Path
import pickle

from injector import Binder, inject, singleton

from . import Configuration
from api import api_pb2 as dto

def bind_repository(binder: Binder):
	binder.bind(Repository, Repository, singleton)

@dataclass
class _Model:
	token: str | None = None
	user: dto.User | None = None
	shop_items: dto.ItemsList | None = None

class Repository:
	@inject
	def __init__(self, config: Configuration):
		self.model = _Model()
		self.path = Path(config.session_file_path())

	def marshal(self):
		with open(self.path, 'wb') as file:
			pickle.dump(self.model, file)
	
	def unmarshal(self):
		if not self.path.exists():
			return
		with open(self.path, 'rb') as file:
			self.model = pickle.load(file)

	def set_token(self, token: str):
		self.model.token = token
		self.marshal()

	def set_user(self, user: dto.User):
		self.model.user = user
		self.marshal()
	
	def set_shop_items(self, items_list: dto.ItemsList):
		self.model.shop_items = items_list
		self.marshal()

	def get_token(self) -> str | None:
		self.unmarshal()
		return self.model.token
	
	def get_user(self) -> dto.User | None:
		self.unmarshal()
		return self.model.user
	
	def get_shop_items(self) -> dto.ItemsList | None:
		self.unmarshal()
		return self.model.shop_items
	
	def clear(self):
		self.path.unlink()
		self.model = _Model()


