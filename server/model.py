from sqlalchemy import Text, BigInteger, Integer, ForeignKey, Identity, Column, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Model(DeclarativeBase):
	pass

def install_model(e: Engine):
	Model.metadata.create_all(e)

class User(Model):
	__tablename__ = "users"

	username: Mapped[str] = mapped_column(Text, primary_key = True)
	balance: Mapped[int] = mapped_column(Integer, default = 0, nullable = False)

class Item(Model):
	__tablename__ = "items"

	id: Mapped[int] = Column("id", Integer, Identity(always = True), primary_key = True)
	name: Mapped[str] = mapped_column(Text, nullable = False)
	price: Mapped[int] = mapped_column(Integer, nullable = False)

	def __str__(self):
		return f"{{id: {self.id}, name: {self.name}, price: {self.price}}}"
