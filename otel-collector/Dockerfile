# First stage: Use Alpine to download and prepare grpc_health_probe
FROM alpine:latest as builder
WORKDIR /build

# Install curl to download grpc_health_probe
RUN apk add --no-cache curl

# Download the grpc_health_probe binary
RUN curl -L -o grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/latest/download/grpc_health_probe-linux-amd64

# Make it executable
RUN chmod +x grpc_health_probe

# Second stage: Use official OpenTelemetry Collector image
FROM otel/opentelemetry-collector:latest

# Copy the grpc_health_probe binary from the builder stage
COPY --from=builder /build/grpc_health_probe /grpc_health_probe

# Ensure it runs as an entrypoint
ENTRYPOINT ["/otelcol"]
