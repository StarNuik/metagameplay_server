from typing import List
from sqlalchemy import select, update, insert
from sqlalchemy.orm import Session
from dependency_injector import providers
from opentelemetry.sdk.trace import Span

from . import *

class DbSessionBase:
	def __init__(self,
		session_factory: providers.Callable[Session],
		tracer_span_factory: providers.Callable[Span]
	):
		self.session = session_factory()
		self.span = tracer_span_factory("db_session")

	def __enter__(self):
		self.session.__enter__()
		self.span.__enter__()
		return self
	
	def __exit__(self, type_, value, traceback):
		self.session.__exit__(type_, value, traceback)
		self.span.__exit__(type_, value, traceback)

	def begin(self):
		return self.session.begin()

class DbSession(DbSessionBase):
	# Read
	def user_exists(self, username: str) -> bool:
		stmt = select(User).where(User.username == username)
		return self.session.scalar(stmt)
	
	def get_user(self, username: str) -> User:
		stmt = select(User).where(User.username == username)
		return self.session.scalars(stmt).one()
	
	def get_all_items(self) -> List[Item]:
		stmt = select(Item)
		return self.session.scalars(stmt).all()
		
	def get_item(self, item_name: str) -> Item | None:
		stmt = select(Item) \
			.where(Item.name == item_name)
		return self.session.scalar(stmt)

	# Write
	def create_user(self, username: str):
		self.session.add(User(username = username))
		
	def add_credits(self, username: str, amount: int):
		stmt = update(User) \
			.where(User.username == username) \
			.values(balance = User.balance + amount)
		self.session.execute(stmt)
	
	def get_item_ownership(self, username: str, item_name: str) -> ItemOwnership | None:
		stmt = select(ItemOwnership) \
			.where(ItemOwnership.owner_username == username) \
			.where(ItemOwnership.item_name == item_name)
		return self.session.scalar(stmt)
	
	def create_item_ownership(self, username: str, item_name: str) -> ItemOwnership:
		stmt = insert(ItemOwnership) \
			.values(
				item_name = item_name,
				owner_username = username,
			).returning(ItemOwnership)
		return self.session.execute(stmt).scalar_one()

	def add_to_item_ownership(self, ownership_id: int, amount: int):
		stmt = update(ItemOwnership) \
			.where(ItemOwnership.id == ownership_id) \
			.values(quantity = ItemOwnership.quantity + amount)
		self.session.execute(stmt)

	def get_all_ownerships(self, username: str) -> list[ItemOwnership]:
		stmt = select(ItemOwnership) \
			.where(ItemOwnership.owner_username == username)
		return self.session.execute(stmt).scalars().all()
