from logging import Logger
from typing import List
from sqlalchemy import select, Engine
from sqlalchemy.orm import Session

from server.model import User

class AuthRepository:
	def __init__(self, database: Engine, logger: Logger):
		self.database = database
		self.log = logger

	def user_exists(self, username: str) -> bool:
		with Session(self.database) as session:
			stmt = select(User).where(User.username == username)
			return session.scalars(stmt).first() != None
	
	def create_user(self, username: str):
		with Session(self.database) as session:
			session.add(
				User(
					username = username,
				)
			)
			session.commit()
