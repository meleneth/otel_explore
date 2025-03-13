from flask import Flask, request, jsonify
import redis
import logging
import threading


from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import set_tracer_provider
from opentelemetry.sdk.logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.logs.export import OTLPLogExporter, BatchLogRecordProcessor
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from prometheus_flask_exporter import PrometheusMetrics

# Set up the tracer provider
resource = Resource.create({"service.name": "flask-api-otel-demo"})
provider = TracerProvider(resource=resource)
set_tracer_provider(provider)
tracer = get_tracer_provider().get_tracer(__name__)

# Set up OTLP Exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
# Initialize OpenTelemetry logging provider
logger_provider = LoggerProvider()
log_exporter = OTLPLogExporter(endpoint="http://otel-collector:4317")  # Adjust if necessary
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

# Use OpenTelemetry logging
otel_logger = logger_provider.get_logger("otel_explore")

# Thread-local storage for worker ID
worker_local = threading.local()

app = Flask(__name__)

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
metrics = PrometheusMetrics(app)
metrics.info("flask_app_info", "Flask App Info", version="1.0.0")

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.before_request
def set_worker_id():
    """Middleware to set worker ID per request."""
    worker_local.worker_id = request.headers.get("X-Worker-ID", "main")

@app.route("/set", methods=["POST"])
def set_value():
    key = request.json.get("key")
    value = request.json.get("value")
    worker_id = getattr(worker_local, "worker_id", "unknown")

    with tracer.start_as_current_span("request_handling") as span:
        if worker_id:
            span.set_attribute("worker_id", worker_id)
            # Create a structured OTel log with attributes
            otel_logger.info(
                "Redis Set Value",
                attributes={"worker_id": worker_id, "route": "/set", "method": request.method}
            )

    with tracer.start_as_current_span("redis_set_value"):
        redis_client.set(key, value)

    with tracer.start_as_current_span("format_return"):
        value = jsonify({"message": f"Set {key} = {value}"})
    return value, 200

@app.route("/get", methods=["GET"])
def get_value():
    key = request.args.get("key")
    worker_id = getattr(worker_local, "worker_id", "unknown")

    with tracer.start_as_current_span("request_handling") as span:
        if worker_id:
            span.set_attribute("worker_id", worker_id)
            # Create a structured OTel log with attributes
            otel_logger.info(
                "Redis Get Value",
                attributes={"worker_id": worker_id, "route": "/get", "method": request.method}
            )

    with tracer.start_as_current_span("redis_get_value"):
        value = redis_client.get(key)
    with tracer.start_as_current_span("format_return"):
        value = jsonify({"message": f"Set {key} = {value}"})

    return value, 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
