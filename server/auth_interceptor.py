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
		if not self.usecase.IsProtectedMethod(handler_call_details.method):
			return continuation(handler_call_details)

		user_session = jwts.from_details(handler_call_details)
		if not self.usecase.IsValidSession(user_session):
			return self.abort_handler

		return continuation(handler_call_details)
	