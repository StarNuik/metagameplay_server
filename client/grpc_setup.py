import grpc
from injector import Module, provider, singleton
# from collections.abc
from opentelemetry.instrumentation.grpc import grpcext

from api import api_pb2_grpc as api
from . import Configuration, LoggingInterceptor, AddSessionInterceptor

type AuthorizedChannel = grpc.Channel
type UnauthorizedChannel = grpc.Channel

class BindGrpc(Module):
	@provider
	@singleton
	def shop_api(self, chan: AuthorizedChannel) -> api.ShopStub:
		return api.ShopStub(chan)

	@provider
	@singleton
	def auth_api(self, chan: UnauthorizedChannel) -> api.AuthStub:
		return api.AuthStub(chan)
	
	@provider
	@singleton
	def unauthorized_channel(
		self,
		config: Configuration,
		logging_interceptor: LoggingInterceptor
	) -> UnauthorizedChannel:
		chan = grpc.insecure_channel(config.hostname())
		chan = grpcext.intercept_channel(chan, logging_interceptor)
		return chan
	
	@provider
	@singleton
	def authorized_channel(
		self,
		chan: UnauthorizedChannel,
		add_session_interceptor: AddSessionInterceptor,
	) -> AuthorizedChannel:
		return grpcext.intercept_channel(chan, add_session_interceptor)