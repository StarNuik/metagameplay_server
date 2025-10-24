from api import api_pb2 as dto



class SessionStorage:
	def save(self, session) -> None:
		print(f"[SessionStorage.save()]\n{session}")
	def read(self) -> dto.UserSession:
		out = dto.UserSession()
		print(f"[SessionStorage.read()]\n{out}")
		return out
	def drop(self) -> None:
		print(f"[SessionStorage.drop()]")