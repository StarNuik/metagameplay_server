import argparse
import collections
import logging
from logging import Logger
from typing import Any
import grpc
from pathlib import Path
from injector import Binder, inject, singleton
from opentelemetry.instrumentation.grpc.grpcext import UnaryClientInterceptor, UnaryClientInfo

from api import api_pb2_grpc as api
from api import api_pb2 as dto
from . import Repository

JWT_HEADER_NAME = "session_token"

def bind_interceptors(binder: Binder):
	binder.bind(AddSessionInterceptor, AddSessionInterceptor, singleton)
	binder.bind(LoggingInterceptor, LoggingInterceptor, singleton)

class AddSessionInterceptor(UnaryClientInterceptor):
	@inject
	def __init__(self, repository: Repository):
		self.repo = repository

	def intercept_unary(self, request, metadata, _, invoker):
		if metadata is None:
			metadata = []
		# raise NotImplementedError()
		metadata.append((JWT_HEADER_NAME, self.repo.get_token()))
		return invoker(request, metadata)

class LoggingInterceptor(UnaryClientInterceptor):
	@inject
	def __init__(self, logger: Logger):
		self.log = logger

	def intercept_unary(self, request, metadata, client_info, invoker):
		method = client_info.full_method
		try:
			self.log.info(f" Request to {method}:\n{request}")
			resp = invoker(request, metadata)
			self.log.info(f" Success response:\n{resp}")
			return resp
		except grpc.RpcError as e:
			self.log.error(f" grpc error: {e.code().value[1], e.details()}")
			raise e
