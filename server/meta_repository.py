from typing import List
from sqlalchemy import select, Engine
import sqlalchemy
from sqlalchemy.orm import Session

from server.model import Item

class MetaRepository:
	def __init__(self, items, database: Engine):
		self.database = database

		with Session(self.database) as session:
			items = map(lambda item : Item(
				name = item["name"],
				price = item["price"],
			), items)
			session.add_all(items)
			session.commit()

	def get_all_items(self) -> List[Item]:
		with Session(self.database) as session:
			stmt = select(Item)

			items = session.scalars(stmt).all()
		return items