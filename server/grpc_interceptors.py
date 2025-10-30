from logging import Logger
import grpc
from injector import Module, multiprovider, singleton
from opentelemetry.instrumentation.grpc._server import _OpenTelemetryServicerContext as ServicerContext
from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor
from opentelemetry.sdk.trace import Tracer

from opentelemetry.instrumentation.grpc._client import OpenTelemetryClientInterceptor

from server import *
from server import jwt_session as jwts
from server import exc


class BindInterceptors(Module):
	@multiprovider
	@singleton
	def interceptors(
		self,
		auth_usecase: AuthUsecase,
		tracer: Tracer,
		logger: Logger,
	) -> list[grpc.ServerInterceptor]:
		return [
			OpenTelemetryServerInterceptor(tracer),
			LoggingInterceptor(logger),
			ExceptionInterceptor(),
			AuthInterceptor(auth_usecase),
		]

class AuthInterceptor(grpc.ServerInterceptor):
	def __init__(self, auth_usecase: AuthUsecase):
		self.auth = auth_usecase

	def raise_exc_handler(self, e: Exception):
		def abort(_, __): raise e
		handler = grpc.unary_unary_rpc_method_handler(abort)
		return handler 

	def intercept_service(self, continuation, handler_call_details):
		user_session = jwts.from_details(handler_call_details)

		e = self.auth.authorization_error(
			handler_call_details.method,
			user_session
		)
		if e is not None:
			return self.raise_exc_handler(e)

		return continuation(handler_call_details)

#SRC https://stackoverflow.com/a/59754982
from opentelemetry.instrumentation.grpc._server import _wrap_rpc_behavior

class ExceptionInterceptor(grpc.ServerInterceptor):
	def intercept_service(self, continuation, handler_call_details):
		def wrapper(behavior, _, __):
			def interceptor(request_or_iterator, context: ServicerContext):
				try:
					return behavior(request_or_iterator, context)
				except exc.UsecaseError as e:
					context.abort(e.code, e.message)
			return interceptor
		
		return _wrap_rpc_behavior(
			continuation(handler_call_details),
			wrapper,
		)
		
class LoggingInterceptor(grpc.ServerInterceptor):
	def __init__(self, logger: Logger):
		self.log = logger
		
	def intercept_service(self, continuation, details: grpc.HandlerCallDetails):
		def wrapper(behavior, _, __):
			def interceptor(request_or_iterator, context: ServicerContext):
				try:
					resp = behavior(request_or_iterator, context)
					self.log.info(f" SCS {details.method}")
					return resp
				except (grpc.RpcError, exc.UsecaseError) as e:
					self.log.warning(f" {e.code.value[0]:3} {details.method}")
					self.log.info(f" error: {e}\nrequest: {request_or_iterator}")
					raise e
				except Exception as e:
					self.log.warning(f" EXC {details.method}")
					self.log.info(f" error: {e}\nrequest: {request_or_iterator}")
					raise e
			return interceptor
		
		return _wrap_rpc_behavior(
			continuation(details),
			wrapper,
		)
		