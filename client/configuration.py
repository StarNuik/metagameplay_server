import logging

from python_json_config import ConfigBuilder

DEFAULT_SESSION_FILE_PATH = "./.client.db"
DEFAULT_HOSTNAME = "localhost:8080"
DEFAULT_LOG_LEVEL = logging.ERROR

class Configuration:
	def __init__(self, path: str):
		builder = ConfigBuilder()
		builder.set_field_access_optional()

		self.config = builder.parse_config(path)

	def session_file_path(self) -> str:
		val = self.config.client.session_file_path
		return val if val is not None else DEFAULT_SESSION_FILE_PATH
	
	def hostname(self) -> str:
		val = self.config.client.hostname
		return val if val is not None else DEFAULT_HOSTNAME
	
	def log_level(self) -> int:
		val = self.config.client.log_level
		try:
			return logging.getLevelNamesMapping()[val]
		except:
			return DEFAULT_LOG_LEVEL