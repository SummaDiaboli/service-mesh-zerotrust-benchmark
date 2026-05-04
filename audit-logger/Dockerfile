# Stage 1: Build the binary
FROM golang:1.23-alpine AS builder

WORKDIR /app

# Copy dependency files first
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Build a static binary
RUN CGO_ENABLED=0 GOOS=linux go build -o audit-logger .

# Stage 2: Final lightweight image
FROM alpine:3.19

# Add curl for security testing and health checks
RUN apk add --no-cache curl

RUN adduser -D -u 10001 appuser
USER appuser

WORKDIR /

COPY --from=builder /app/audit-logger /audit-logger

EXPOSE 8080

CMD ["/audit-logger"]
