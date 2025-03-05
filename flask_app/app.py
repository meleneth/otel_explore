from flask import Flask, request, jsonify
import redis
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import set_tracer_provider

app = Flask(__name__)

# OpenTelemetry Setup
set_tracer_provider(TracerProvider())
tracer = set_tracer_provider().get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
tracer.provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Redis Connection
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

@app.route("/set", methods=["POST"])
def set_value():
    key = request.json.get("key")
    value = request.json.get("value")
    
    with tracer.start_as_current_span("flask_set_value"):
        redis_client.set(key, value)

    return jsonify({"message": f"Set {key} = {value}"}), 200

@app.route("/get", methods=["GET"])
def get_value():
    key = request.args.get("key")
    
    with tracer.start_as_current_span("flask_get_value"):
        value = redis_client.get(key)

    return jsonify({"value": value}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
