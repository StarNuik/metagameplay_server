import grpc
from pathlib import Path
from opentelemetry.instrumentation.grpc._server import _OpenTelemetryServicerContext as ServicerContext
from dependency_injector.containers import DynamicContainer
from dependency_injector import providers
from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor
from opentelemetry.sdk.trace import TracerProvider, Span, Tracer

from server import *
from server import jwt_session as jwts
from server import exc

import injector

class BindInterceptors(injector.Module):
	@injector.multiprovider
	def interceptors(
		self,
		auth_usecase: AuthUsecase,
		tracer: Tracer
	) -> list[grpc.ServerInterceptor]:
		return [
			OpenTelemetryServerInterceptor(tracer),
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
		
	