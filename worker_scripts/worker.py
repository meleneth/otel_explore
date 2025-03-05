import requests
import random
import time
import uuid
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Generate unique runner ID
RUNNER_ID = str(uuid.uuid4())
# Set up the tracer provider
resource = Resource.create({"service.name": f"flask-worker-{RUNNER_ID}"})
provider = TracerProvider(resource=resource)
set_tracer_provider(provider)  # ✅ Correct way to set it
tracer = get_tracer_provider().get_tracer(__name__)  # ✅ Correct way to get the tracer

# Set up OTLP Exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

FLASK_APP_URL = "http://flask-app:5000"

while True:
    key = f"key-{random.randint(1, 100)}"
    value = f"value-{random.randint(1, 1000)}"

    # Send request to Flask app
    with tracer.start_as_current_span("worker_set_request"):
        response = requests.post(f"{FLASK_APP_URL}/set", json={"key": key, "value": value})

    print(f"Runner {RUNNER_ID}: Set {key} = {value}, Response: {response.status_code}")
    time.sleep(random.uniform(0.5, 2))
