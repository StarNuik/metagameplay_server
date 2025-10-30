from logging import Logger
import logging
from injector import Module, provider, singleton

from . import Configuration

class BindInfra(Module):
	@provider
	@singleton
	def logger(self, config: Configuration) -> Logger:
		logging.basicConfig(
			level = config.log_level(),
		)
		return logging.getLogger(" client")