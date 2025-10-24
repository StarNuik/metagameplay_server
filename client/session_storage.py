from api import api_pb2 as dto
from abc import ABC, abstractmethod
from client import UserSession

class SessionStorage(ABC):
	@abstractmethod
	def save(self, session: UserSession) -> None:
		pass
	
	@abstractmethod
	def read(self) -> UserSession:
		pass

	@abstractmethod
	def drop(self) -> None:
		pass

class StubSessionStorage(SessionStorage):
	def save(self, session: UserSession) -> None:
		print(f"[StubSessionStorage.save()]\n{session}")
	
	def read(self) -> UserSession:
		raise NotImplementedError("No session was saved")

	def drop(self) -> None:
		print(f"[StubSessionStorage.drop()]")
	
