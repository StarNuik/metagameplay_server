import pickle
import os
from pathlib import Path

from client import SessionStorage, UserSession

# def __open(path: Path):
# 	file = open(path, "rb+")
# 	return file

class PathError(Exception):
	pass

class FileSessionStorage(SessionStorage):
	def __init__(self, path: Path):
		if path.is_dir():
			raise PathError("provided path is a directory: {path}")
		if not path.parent.exists():
			raise PathError("directory doesn't exist: {path}")
		
		self.path = path

	def save(self, session: UserSession) -> None:
		with open(self.path, "wb") as file:
			pickle.dump(session, file)
	
	def read(self) -> UserSession:
		if not self.path.exists():
			return None

		with open(self.path, "rb") as file:
			session = pickle.load(file)
		
		if not isinstance(session, UserSession):
			return None
		
		return session

	def drop(self) -> None:
		self.path.unlink(missing_ok = True)