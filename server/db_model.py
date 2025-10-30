from sqlalchemy import Text, Integer, ForeignKey, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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
		return f"{{name: {self.name}, price: {self.price}}}"

class ItemOwnership(_Table):
	__tablename__ = "item_ownership"

	# sqlite only
	id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement = True)
	# id: Mapped[int] = Column("id", BigInteger, Identity(always = True), primary_key = True)
	quantity: Mapped[int] = mapped_column(Integer, nullable = False, default = 0)
	
	item_name: Mapped[str] = mapped_column(ForeignKey("items.name"))
	owner_username: Mapped[str] = mapped_column(ForeignKey("users.username"))

	def __str__(self):
		return f"{{id: {self.id}, item_name: {self.item_name}, owner_username: {self.owner_username}, quantity: {self.quantity}}}"

