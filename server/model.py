import sqlalchemy

from sqlalchemy.exc import IntegrityError
from sqlalchemy import Text, Integer, ForeignKey, Engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from dependency_injector import providers

class _Table(DeclarativeBase):
	pass

class User(_Table):
	__tablename__ = "users"

	username: Mapped[str] = mapped_column(Text, primary_key = True)
	balance: Mapped[int] = mapped_column(Integer, default = 0, nullable = False)

class Item(_Table):
	__tablename__ = "items"

	name: Mapped[str] = mapped_column(Text, primary_key = True, nullable = False)
	price: Mapped[int] = mapped_column(Integer, nullable = False)

	def __str__(self):
		return f"{{id: {self.id}, name: {self.name}, price: {self.price}}}"

def install_model(engine: Engine):
	_Table.metadata.create_all(engine)

class Model:
	def __init__(self,
		session_factory: providers.Callable[Session],
		item_list_factory: providers.Callable[list[Item]],
	):
		self.session = session_factory

		try:
			self.create_items(item_list_factory())
		except IntegrityError:
			pass

	# Read
	def user_exists(self, username: str) -> bool:
		with self.session() as session:
			stmt = select(User).where(User.username == username)
			return session.scalars(stmt).first() != None
	
	def get_user(self, username: str) -> User:
		with self.session() as session:
			stmt = select(User).where(User.username == username)
			return session.scalars(stmt).one()
	
	def get_all_items(self) -> list[Item]:
		with self.session() as session:
			stmt = select(Item)
			return session.scalars(stmt).all()

	# Modify
	def create_items(self, items: list[Item]):
		with self.session() as session:
			session.add_all(items)
			session.commit()
	
	def create_user(self, username: str):
		with self.session() as session:
			session.add(User(username = username))
			session.commit()
		
	def add_credits(self, username: str, amount: int):
		with self.session() as session:
			stmt = update(User) \
				.where(User.username == username) \
				.values(balance = User.balance + amount)
			session.execute(stmt)
			session.commit()