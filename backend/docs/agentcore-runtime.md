# AgentCore Runtime Notes

This document describes the minimal AgentCore Runtime integration used by the backend.

## Client API

The backend uses the AWS SDK client:
- boto3 client name: bedrock-agentcore
- method: invoke_agent_runtime
- parameters: agentRuntimeArn, runtimeSessionId, payload (bytes)

The runtime ARN is required by InvokeAgentRuntime. If you only have a runtime ID,
resolve its ARN before calling the runtime.

## Contract

Input JSON:
- cv_text (string, required)
- job_offer (string or object, optional)

Output JSON:
- score (int)
- summary (string)
- skills (list of strings)
- experience (string)

The runtime may include experience_summary as an alias for experience for
compatibility with backend parsing.

## Local test

Run the runtime locally from its folder:

python app.py

If BedrockAgentCoreApp is installed, use LOCAL_TEST=true to run the local test
instead of app.run().
