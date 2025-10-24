from api import api_pb2 as dto
from abc import ABC, abstractmethod

class SessionStorage(ABC):
	@abstractmethod
	def save(self, session) -> None:
		pass
	
	@abstractmethod
	def read(self) -> dto.UserSession:
		pass

	@abstractmethod
	def drop(self) -> None:
		pass

class StubSessionStorage(SessionStorage):
	def save(self, session) -> None:
		print(f"[StubSessionStorage.save()]\n{session}")
	
	def read(self) -> dto.UserSession:
		out = dto.UserSession()
		print(f"[StubSessionStorage.read()]\n{out}")
		return out

	def drop(self) -> None:
		print(f"[StubSessionStorage.drop()]")
	
