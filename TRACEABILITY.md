# Traceability Guide

## Overview

The Agent Orchestrator service includes comprehensive traceability features to track and debug requests through the system. Each request is assigned a unique trace ID that flows through all components.

## Features

### 1. **Request Trace IDs**

Every API request receives a unique trace ID (UUID v4) that:
- Is included in the API response as `trace_id` field
- Is added to HTTP response headers as `X-Trace-ID`
- Flows through all internal components and logs
- Persists across disambiguation flows

### 2. **Structured Logging**

All log messages include:
- **Timestamp**: When the event occurred
- **Trace ID**: The unique request identifier
- **Log Level**: INFO, WARNING, ERROR, etc.
- **Component**: Which module generated the log
- **Message**: Contextual information

#### Log Format
```
YYYY-MM-DD HH:MM:SS | trace-id | LEVEL    | module.name | message
```

#### Example Logs
```
2026-01-03 10:15:23 | 74a3bd84-1285-461d | INFO     | app.main | Incoming request: POST /chat
2026-01-03 10:15:23 | 74a3bd84-1285-461d | INFO     | app.main | Chat request - session: demo_user_1, message: Is my car AB-123-CD allowed to enter...
2026-01-03 10:15:23 | 74a3bd84-1285-461d | INFO     | app.graph | [demo_user_1] extract_intent_node - message: Is my car AB-123-CD allowed to enter...
2026-01-03 10:15:24 | 74a3bd84-1285-461d | INFO     | app.graph | [demo_user_1] Intent extracted: single_car, city: Amsterdam, car: AB-123-CD
2026-01-03 10:15:24 | 74a3bd84-1285-461d | INFO     | app.graph | [demo_user_1] resolve_car_node - intent: single_car, identifier: AB-123-CD
2026-01-03 10:15:24 | 74a3bd84-1285-461d | INFO     | app.graph | [demo_user_1] Car resolved: AB-123-CD
2026-01-03 10:15:24 | 74a3bd84-1285-461d | INFO     | app.graph | [demo_user_1] resolve_zone_node - city: Amsterdam, phrase: city center
2026-01-03 10:15:24 | 74a3bd84-1285-461d | INFO     | app.graph | [demo_user_1] Zone disambiguation needed - 2 candidates
2026-01-03 10:15:24 | 74a3bd84-1285-461d | INFO     | app.main | Graph completed - session: demo_user_1, pending_question: True
```

### 3. **Graph Node Tracking**

Each graph node execution is logged with:
- Session ID in brackets: `[demo_user_1]`
- Node name: `extract_intent_node`, `resolve_car_node`, etc.
- Key state information: intent, identifiers, results

#### Tracked Nodes
- `extract_intent_node` - Intent and slot extraction
- `resolve_car_node` - Car resolution and disambiguation
- `resolve_zone_node` - Zone resolution and disambiguation
- `fetch_policy_node` - Policy retrieval
- `decide_node` - Eligibility decision making
- `explain_node` - Final response generation

### 4. **Error Tracking**

Errors include:
- Full stack traces
- Trace ID for correlation
- Session context
- Error details

```
2026-01-03 10:15:25 | de050027-54b5-4d47 | ERROR    | app.main | Error processing request - session: demo_user_1, error: ...
```

## Usage

### API Response

Each API response includes the trace ID:

```json
{
  "session_id": "demo_user_1",
  "reply": "Your vehicle is allowed...",
  "pending_question": false,
  "options": null,
  "state": null,
  "trace_id": "74a3bd84-1285-461d-9fd5-b120a79e4876"
}
```

### HTTP Headers

The trace ID is also available in response headers:

```bash
curl -i http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user1", "message": "Check my car"}'

# Response includes:
# X-Trace-ID: 74a3bd84-1285-461d-9fd5-b120a79e4876
```

### Debugging a Request

To debug a specific request:

1. **Capture the trace ID** from the API response or HTTP header
2. **Search server logs** for that trace ID:
   ```bash
   grep "74a3bd84-1285-461d" server.log
   ```
3. **Follow the flow** through all logged steps
4. **Identify issues** by examining state at each node

### Example: Tracing a Complete Flow

```bash
# Make a request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user1", "message": "Is AB-123-CD allowed?"}'

# Response includes trace_id: "abc-123-def"

# Search logs for this trace
grep "abc-123-def" logs/app.log
```

Output shows the complete flow:
```
10:15:23 | abc-123-def | INFO | Incoming request: POST /chat
10:15:23 | abc-123-def | INFO | Chat request - session: user1
10:15:23 | abc-123-def | INFO | [user1] extract_intent_node
10:15:24 | abc-123-def | INFO | [user1] Intent extracted: single_car
10:15:24 | abc-123-def | INFO | [user1] resolve_car_node
10:15:24 | abc-123-def | INFO | [user1] Car resolved: AB-123-CD
10:15:24 | abc-123-def | INFO | [user1] resolve_zone_node
10:15:24 | abc-123-def | INFO | [user1] Zone disambiguation needed
10:15:25 | abc-123-def | INFO | Graph completed - pending_question: True
10:15:25 | abc-123-def | INFO | Request completed - Status: 200
```

## Configuration

### Log Level

Adjust logging verbosity by setting the log level in `app/logging_config.py`:

```python
root_logger.setLevel(logging.INFO)  # Change to DEBUG for more detail
```

### Log Format

Customize the log format in `TraceFormatter`:

```python
formatter = TraceFormatter(
    '%(asctime)s | %(trace_id)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

## Benefits

1. **Request Correlation**: Link all logs for a single request using trace ID
2. **Multi-step Tracking**: Follow disambiguation flows across multiple API calls
3. **Performance Analysis**: Measure time spent in each node
4. **Error Diagnosis**: Quickly identify where failures occur
5. **Session Debugging**: Track user sessions across multiple requests
6. **Production Monitoring**: Monitor system behavior in production

## Best Practices

1. **Always log trace IDs** when reporting issues
2. **Include trace IDs** in error reports to support teams
3. **Store logs centrally** for easier searching and analysis
4. **Monitor trace ID patterns** for system health
5. **Use trace IDs** for performance profiling
6. **Archive logs** with trace IDs for compliance and auditing

## Integration with Monitoring Tools

The structured log format is compatible with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch**
- **Grafana Loki**

Example Logstash configuration:
```ruby
filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} \| %{UUID:trace_id} \| %{LOGLEVEL:level} \| %{DATA:module} \| %{GREEDYDATA:log_message}" }
  }
}
```

## Testing Traceability

Run the test script to see traceability in action:

```bash
./test_api.sh
```

Each example will display:
- 📨 User input
- 🔍 Trace ID for the request
- Complete API response with trace_id field
- Trace ID for disambiguation responses

Check server logs to see the corresponding structured log entries with matching trace IDs.
