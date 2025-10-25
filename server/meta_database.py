from typing import List
from sqlalchemy import Text, BigInteger, Integer, ForeignKey, create_engine, select, Identity, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

class Base(DeclarativeBase):
	pass

class Item(Base):
	__tablename__ = "items"

	id: Mapped[int] = Column("id", Integer, Identity(always = True), primary_key = True)
	name: Mapped[str] = mapped_column(Text)
	price: Mapped[int] = mapped_column(Integer)

	def __str__(self):
		return f"{{id: {self.id}, name: {self.name}, price: {self.price}}}"

class MetaDatabase:
	def __init__(self, items):
		self.engine = create_engine("sqlite:///db.sqlite3", echo = True)
		Base.metadata.create_all(self.engine)

		with Session(self.engine) as session:
			items = map(lambda item : Item(
				name = item["name"],
				price = item["price"],
			), items)
			session.add_all(items)
			session.commit()
				
		pass

	def get_all_items(self) -> List[Item]:
		with Session(self.engine) as session:
			stmt = select(Item)

			items = session.scalars(stmt).all()
		return items