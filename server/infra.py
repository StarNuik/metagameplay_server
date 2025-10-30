from logging import Logger
import logging
from injector import provider, Module, singleton
from opentelemetry.sdk.trace import TracerProvider, Span, Tracer
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.grpc._server import OpenTelemetryServerInterceptor
from opentelemetry.instrumentation.grpc._server import _OpenTelemetryServicerContext as ServicerContext
from collections.abc import Callable

type TracerSpanFactory = Callable[[str], Span]

class BindInfra(Module):
	@provider
	def logger(self) -> Logger:
		return logging.getLogger(__name__)

	@provider
	@singleton
	def tracer(self) -> Tracer:
		provider = TracerProvider()
		exporter = BatchSpanProcessor(OTLPSpanExporter())
		provider.add_span_processor(exporter)

		trace.set_tracer_provider(provider)

		tracer = trace.get_tracer(__name__)
		return tracer

	@provider
	def span_factory(self, tracer: Tracer) -> TracerSpanFactory:
		return lambda name : tracer.start_as_current_span(name)