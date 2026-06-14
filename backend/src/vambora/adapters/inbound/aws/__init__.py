"""AWS Lambda entrypoints (inbound adapters).

Two handlers back the serverless deployment (see plan.md decision #15 and
docs/operations/aws-serverless.md):

- ``api_handler.handler`` — the FastAPI app behind a Lambda function URL,
  adapted to the Lambda event/response shape by Mangum.
- ``poller_handler.handler`` — a scheduled Lambda that does one ingest +
  alert-evaluation + compaction pass per invocation, replacing the long-lived
  poller/evaluator tasks that ``main.py`` runs locally.

These are thin: they build the same ``Container`` as every other entrypoint and
delegate to the application layer.
"""
