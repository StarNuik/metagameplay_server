import json
import grpc
import jwt
from jwt.exceptions import PyJWTError

JWT_SECRET = "meow"
JWT_ALGO = "HS256"
JWT_PAYLOAD_KEY = "__payload"
JWT_HEADER = "session_token"

class Session():
	def __init__(self, username):
		self.username = username
	def to_json(self):
		return json.dumps(self, default = lambda obj : obj.__dict__)

def from_json(jsn: str) -> Session:
	dct = json.loads(jsn)
	return Session(dct["username"])

def pack(payload: Session) -> str:
	jwt_payload = {
		JWT_PAYLOAD_KEY: payload.to_json(),
	}
	token = jwt.encode(jwt_payload, JWT_SECRET, algorithm = JWT_ALGO)
	return token

def unpack(token: str) -> Session | None:
	try:
		jwt_payload = jwt.decode(token, JWT_SECRET, algorithms = [JWT_ALGO])
		payload_string = jwt_payload[JWT_PAYLOAD_KEY]
		payload = from_json(payload_string)
		return payload
	except PyJWTError:
		return None

def from_metadata(metadata: dict[str, str | bytes]) -> Session | None:
	if not JWT_HEADER in metadata:
		return None
	token = metadata[JWT_HEADER]

	payload = unpack(token)
	return payload

def from_details(details: grpc.HandlerCallDetails) -> Session | None:
	metadata = dict(details.invocation_metadata)
	return from_metadata(metadata)

def from_context(context: grpc.ServicerContext) -> Session | None:
	metadata = dict(context.invocation_metadata())
	return from_metadata(metadata)