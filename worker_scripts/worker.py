import requests
import random
import time
from opentelemetry.trace import set_tracer_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# OpenTelemetry Setup
set_tracer_provider(TracerProvider())
tracer = set_tracer_provider().get_tracer(__name__)
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
tracer.provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

FLASK_APP_URL = "http://flask-app:5000"

while True:
    key = f"key-{random.randint(1, 100)}"
    value = f"value-{random.randint(1, 1000)}"

    # Send request to Flask app
    with tracer.start_as_current_span("worker_set_request"):
        response = requests.post(f"{FLASK_APP_URL}/set", json={"key": key, "value": value})
    
    print(f"Set {key} = {value}, Response: {response.status_code}")
    time.sleep(random.uniform(0.5, 2))
