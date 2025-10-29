import grpc
from pathlib import Path
from opentelemetry.instrumentation.grpc._server import _OpenTelemetryServicerContext as ServicerContext

from server import *
from server import jwt_session as jwts
from server import exc

class AuthInterceptor(grpc.ServerInterceptor):
	def __init__(self, auth_usecase: AuthUsecase):
		self.usecase = auth_usecase

		def abort(_, context: ServicerContext):
			context.abort(grpc.StatusCode.UNAUTHENTICATED, exc.UNAUTHENTICATED_MESSAGE)

		self.abort_handler = grpc.unary_unary_rpc_method_handler(abort)

	def intercept_service(self, continuation, handler_call_details):
		user_session = jwts.from_details(handler_call_details)
		if self.usecase.is_authorized(
			handler_call_details.method,
			user_session,
		):
			return continuation(handler_call_details)
		else:
			return self.abort_handler

#SRC https://stackoverflow.com/a/59754982
from opentelemetry.instrumentation.grpc._server import _wrap_rpc_behavior

class ExceptionInterceptor(grpc.ServerInterceptor):
	def intercept_service(self, continuation, handler_call_details):
		def wrapper(behavior, request_streaming, response_streaming):
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
		
	