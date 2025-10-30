import random
from dependency_injector import providers
import injector
from api import api_pb2 as dto

from server import *
from server import jwt_session as jwts
from server import exc

def bind_shop_usecase(binder: injector.Binder):
	binder.bind(ShopUsecase, to = ShopUsecase, scope = injector.singleton)

class ShopUsecase:
	@injector.inject
	def __init__(self, config: Configuration):
		self.reward_range = config.reward

	def reward_amount(self) -> int:
		return random.randrange(self.reward_range["min"], self.reward_range["max"])
		
	def get_user(self, db: DbSession, user_session: jwts.Session) -> dto.User:
		username = user_session.username
		user = db.get_user(username)
		items = []

		for ownership in db.get_all_ownerships(username):
			if ownership.quantity <= 0:
				continue
			
			items.append(dto.OwnedItem(
				name = ownership.item_name,
				quantity = ownership.quantity,
			))
		
		return dto.User(
			username = username,
			credits = user.balance,
			items = items,
		)
	
	def receive_login_reward(self, db: DbSession, user_session: jwts.Session):
		reward = self.reward_amount()
		db.add_credits(user_session.username, reward)
	
	def get_shop_items(self, db: DbSession):
		items = db.get_all_items()
		items = dto.ItemsList(
			items = map(
				lambda item : dto.Item(
					name = item.name,
					price = item.price
				), items
			)
		)
		return items
	
	def buy_item(self, db: DbSession, req: dto.BuyItemReq, user_session: jwts.Session):
		if not req.item_name:
			raise exc.EmptyItemNameError
		
		item = db.get_item(req.item_name)
		if item is None:
			raise exc.InvalidItemError
	
		user = db.get_user(user_session.username)
		if item.price > user.balance:
			raise exc.NotEnoughCreditsError
	
		ownership = db.get_item_ownership(user.username, item.name)
		if ownership is None:
			ownership = db.create_item_ownership(user.username, item.name)

		db.add_credits(user.username, -item.price)
		db.add_to_item_ownership(ownership.id, 1)
	
	def sell_item(self, db: DbSession, req: dto.SellItemReq, user_session: jwts.Session):
		if not req.item_name:
			raise exc.InvalidItemError

		username = user_session.username

		ownership = db.get_item_ownership(username, req.item_name)
		if ownership is None or ownership.quantity <= 0:
			raise exc.NotEnoughItemsError

		item = db.get_item(req.item_name)
		
		db.add_credits(username, item.price)
		db.add_to_item_ownership(ownership.id, -1)
	
	
