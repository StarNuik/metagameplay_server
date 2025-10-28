import sqlalchemy

from sqlalchemy.exc import IntegrityError
from sqlalchemy import Text, Integer, BigInteger, Column, Identity, ForeignKey, Engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, attribute_keyed_dict
from dependency_injector import providers
from opentelemetry.sdk.trace import Span

class _Table(DeclarativeBase):
	pass

class User(_Table):
	__tablename__ = "users"

	username: Mapped[str] = mapped_column(Text, primary_key = True)
	balance: Mapped[int] = mapped_column(Integer, default = 0, nullable = False)

	# TODO: remove rel
	owned_items: Mapped[dict[str, "ItemOwnership"]] = relationship(
		back_populates = "owner",
		collection_class = attribute_keyed_dict("item_name"),
	)

class Item(_Table):
	__tablename__ = "items"

	name: Mapped[str] = mapped_column(Text, primary_key = True, nullable = False)
	price: Mapped[int] = mapped_column(Integer, nullable = False)

	def __str__(self):
		return f"{{name: {self.name}, price: {self.price}}}"

class ItemOwnership(_Table):
	__tablename__ = "item_ownership"

	# sqlite only
	id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement = True)
	# id: Mapped[int] = Column("id", BigInteger, Identity(always = True), primary_key = True)
	quantity: Mapped[int] = mapped_column(Integer, nullable = False, default = 0)
	
	item_name: Mapped[str] = mapped_column(ForeignKey("items.name"))
	owner_username: Mapped[str] = mapped_column(ForeignKey("users.username"))

	# TODO: remove rel
	item: Mapped["Item"] = relationship()
	owner: Mapped["User"] = relationship(back_populates = "owned_items")

	def __str__(self):
		return f"{{id: {self.id}, item_name: {self.item_name}, owner_username: {self.owner_username}, quantity: {self.quantity}}}"

def install_model(engine: Engine):
	_Table.metadata.create_all(engine)

def migrate_items(engine: Engine, item_list: list[Item]):
	try:
		with Session(engine) as session, session.begin():
			session.add_all(item_list)
			session.commit()
	except IntegrityError:
		pass

class DbSession:
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
	
	# Read
	def user_exists(self, username: str) -> bool:
		stmt = select(User).where(User.username == username)
		return self.session.scalar(stmt)
	
	def get_user(self, username: str) -> User:
		stmt = select(User).where(User.username == username)
		return self.session.scalars(stmt).one()
	
	def get_all_items(self) -> list[Item]:
		stmt = select(Item)
		return self.session.scalars(stmt).all()
		
	def get_item(self, item_name: str) -> Item | None:
		stmt = select(Item) \
			.where(Item.name == item_name)
		return self.session.scalar(stmt)

	# Modify
	def create_user(self, username: str):
		self.session.add(User(username = username))
		
	def add_credits(self, username: str, amount: int):
		stmt = update(User) \
			.where(User.username == username) \
			.values(balance = User.balance + amount)
		self.session.execute(stmt)
	
	def add_item_ownership(self, user: User, item: Item, amount: int):
		# TODO: these are implicit sql calls
		if not item.name in user.owned_items:
			user.owned_items[item.name] = ItemOwnership(
				quantity = amount,
				owner_username = user.username,
				item_name = item.name,
			)
		else:
			user.owned_items[item.name].quantity += amount


	