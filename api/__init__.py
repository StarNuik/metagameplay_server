from importlib import import_module
import sys

_messages_module = import_module(".api_pb2", package=__name__)

sys.modules.setdefault("api_pb2", _messages_module)