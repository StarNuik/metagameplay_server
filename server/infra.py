from logging import Logger
import logging
from injector import provider, Module, singleton
from opentelemetry.sdk.trace import TracerProvider, Span, Tracer
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from collections.abc import Callable

from . import Configuration

type TracerSpanFactory = Callable[[str], Span]

class BindInfra(Module):
	@provider
	@singleton
	def logger(self, config: Configuration) -> Logger:
		logging.basicConfig(
			level = config.log_level(),
		)
		return logging.getLogger()

	@provider
	@singleton
	def tracer(self) -> Tracer:
		resource = Resource.create({
			"service.name": "shop_service"
		})
		provider = TracerProvider(resource = resource)
		exporter = BatchSpanProcessor(OTLPSpanExporter())
		provider.add_span_processor(exporter)

		trace.set_tracer_provider(provider)

		tracer = trace.get_tracer(__name__)
		return tracer

	@provider
	@singleton
	def span_factory(self, tracer: Tracer) -> TracerSpanFactory:
		return lambda name : tracer.start_as_current_span(name)