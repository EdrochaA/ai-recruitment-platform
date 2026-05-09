# AgentCore Runtime Integration Guide

## Overview

The CV Analyzer now supports integration with **AWS Bedrock AgentCore** for intelligent CV analysis. This guide explains how to configure and use the AgentCore runtime for CV analysis.

### What is AgentCore?

AWS Bedrock AgentCore is a managed service that orchestrates interactions with foundation models (LLMs) and external tools. In this project, it's used to:

- Perform intelligent CV analysis using Claude Sonnet (or similar LLM)
- Extract skills, experience, and compatibility scores
- Generate detailed assessments of candidate fit

## Architecture

```
POST /applications/{id}/cv/analyze
     ↓
AnalyzeApplicationCV (Use Case)
     ↓
CVAnalyzer (Port)
     ↓
AgentCoreCVAnalyzer (Adapter)
     ↓
AgentCoreClient (AWS Integration)
     ↓
boto3: bedrock-agentcore (InvokeAgentRuntime)
     ↓
AWS Bedrock AgentCore Runtime
     ↓
Claude LLM (Bedrock)
```

The architecture maintains **clean separation of concerns**:
- **Domain**: `CVAnalyzer` port (interface only, no AWS)
- **Application**: `AnalyzeApplicationCV` use case (orchestration, no AWS)
- **Adapters**: `AgentCoreCVAnalyzer` and `AgentCoreClient` (AWS-specific)

If AgentCore is unavailable or misconfigured, the system automatically falls back to `SimpleCVAnalyzer` (local heuristic-based analysis).

## Configuration

### Environment Variables

To activate AgentCore mode, set the following environment variables:

```bash
# Enable AgentCore provider (default: "simple")
export CV_ANALYZER_PROVIDER=agentcore

# AWS Region (default: "eu-west-1")
export AWS_REGION=eu-west-1

# AgentCore Runtime ID or ARN (at least ONE required for agentcore mode)
export AGENTCORE_RUNTIME_ID=cv-analyzer-abc123
# OR
export AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/cv-analyzer-abc123

# Optional: Strands Agent ID within the runtime (default: "cv-analyzer-agent")
export AGENTCORE_AGENT_ID=cv-analyzer-agent-v1

# Optional: Bedrock model ID (default: Claude Sonnet)
export BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-20250514-v1:0

# AWS Credentials (if not using default AWS profile)
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
# Optional for temporary credentials
export AWS_SESSION_TOKEN=your_session_token
# OR use a named profile:
export AWS_PROFILE=your-profile-name
```

### Configuration Priority

1. **Runtime Identifier** (required):
  - The AWS SDK InvokeAgentRuntime call requires the **Agent Runtime ARN**
  - Set `AGENTCORE_RUNTIME_ARN` whenever possible
  - `AGENTCORE_RUNTIME_ID` is accepted only if it already contains an ARN
  - If neither is set, automatically falls back to `SimpleCVAnalyzer`

2. **AWS Credentials**:
   - Uses AWS SDK credential chain:
     1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
     2. AWS credentials file (`~/.aws/credentials`)
     3. Named profile (`AWS_PROFILE`)
     4. IAM role (if running on EC2/ECS/Lambda)

3. **Region**:
   - Defaults to `eu-west-1`
   - Override with `AWS_REGION`

### Example Configurations

#### Development (Mock Mode - No AWS Required)
```bash
# Uses SimpleCVAnalyzer, no AWS credentials needed
export CV_ANALYZER_PROVIDER=simple
```

#### Development with AgentCore (Local AWS Credentials)
```bash
export CV_ANALYZER_PROVIDER=agentcore
export AGENTCORE_RUNTIME_ID=local-dev-xyz123
export AWS_REGION=eu-west-1
# Credentials loaded from ~/.aws/credentials or environment
```

#### Production (CI/CD, IAM Role)
```bash
export CV_ANALYZER_PROVIDER=agentcore
export AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/prod-cv-analyzer
export AWS_REGION=eu-west-1
# Credentials from IAM role attached to EC2/ECS/Lambda
```

## How to Obtain Runtime ID/ARN

### Step 1: Deploy AgentCore Runtime

If you haven't already deployed an AgentCore runtime, use the **blueprint** from `cc-swp-blueprint-agent-memory`:

```bash
cd /path/to/cc-swp-blueprint-agent-memory
# Follow the deployment instructions in that project's README
# This will create a runtime and output the ARN
```

### Step 2: Extract Runtime ID

From the ARN `arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/cv-analyzer-abc123`:
- **Runtime ID**: `cv-analyzer-abc123`
- **Full ARN**: The entire string

### Step 3: Verify Access

```bash
# Test AWS credentials
aws bedrock-agentcore-control describe-runtime \
  --runtime-identifier cv-analyzer-abc123 \
  --region eu-west-1
```

## Testing the Endpoint

### Using Mock Mode (No AWS)
```bash
export CV_ANALYZER_PROVIDER=simple

curl -X POST http://localhost:8000/applications/{id}/cv/analyze
```

### Using AgentCore (With AWS)

**Step 1: Create a job application with CV**

```bash
# 1. Create a job offer
curl -X POST http://localhost:8000/job_offers \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "Required: Python, FastAPI, PostgreSQL, Docker, AWS"
  }'
# Returns: {"id": "offer-123", ...}

# 2. Upload a CV (as PDF)
curl -X POST http://localhost:8000/applications/app-123/cv \
  -F "file=@candidate_cv.pdf"

# 3. Process the CV (extract text)
curl -X POST http://localhost:8000/applications/app-123/cv/process

# 4. Analyze the CV with AgentCore
curl -X POST http://localhost:8000/applications/app-123/cv/analyze
```

**Step 2: Check results**

```bash
# Retrieve the analyzed application
curl http://localhost:8000/applications/app-123
```

Expected response includes:
```json
{
  "id": "app-123",
  "cv_analysis_status": "completed",
  "cv_analysis_score": 85,
  "cv_analysis_summary": "Candidate is well-aligned with role requirements...",
  "cv_analysis_skills": ["python", "fastapi", "docker", "aws"],
  "cv_analysis_experience": "8+ years in backend development...",
  "cv_analyzed_at": "2024-05-09T14:30:00Z"
}
```

## Understanding the Analysis Process

### Flow

1. **Request Arrives**: `POST /applications/{id}/cv/analyze`
2. **Validate**: Check CV text exists, job description exists
3. **Build Prompt**: Create analysis prompt with CV and job description
4. **Invoke AgentCore**: Call boto3 bedrock-agentcore client (InvokeAgentRuntime)
5. **Generate Session**: Create unique session ID for traceability
6. **LLM Analysis**: AgentCore routes to Claude for analysis
7. **Parse Response**: Extract JSON from LLM response
8. **Validate**: Ensure required fields present and valid
9. **Normalize**: Convert to internal format
10. **Save Results**: Update JobApplication entity
11. **Return**: HTTP 200 with updated application

### LLM Prompt

The system sends a structured prompt to AgentCore:

```
Analyze the following CV against the job description and respond with a JSON object.

CANDIDATE'S CV:
---
[CV text here]
---

JOB DESCRIPTION:
---
[Job description here]
---

Please analyze this CV against the job requirements and return a JSON object with these exact fields:
{
    "skills": ["skill1", "skill2", ...],
    "experience_summary": "A brief summary of relevant experience",
    "score": 0,
    "summary": "Overall assessment of candidate fit (1-2 sentences)"
}

Requirements:
- skills: List all detected technical and professional skills from the CV (max 10)
- experience_summary: Extract and summarize relevant professional experience (max 200 chars)
- score: Rate compatibility 0-100 (0=no fit, 50=partial fit, 100=excellent fit)
- summary: Provide a concise assessment of the candidate's suitability for the role

Return ONLY the JSON object. No additional text before or after.
```

### Response Parsing

AgentCoreClient robustly handles various response formats:

1. **Direct JSON**: `{"skills": [...], ...}`
2. **Markdown wrapped**: `` ```json {...} ``` ``
3. **JSON in text**: Text containing `{...}`
4. **Malformed**: Attempts extraction and validation

If parsing fails, the request returns HTTP 400 with error details.

### Logging

The system logs key information (without exposing sensitive data):

```
INFO | AgentCoreClient initialized for AgentCore runtime. Region: eu-west-1, Agent: cv-analyzer-agent
INFO | Invoking AgentCore runtime. session_id=cv-analysis-1715..., actor_id=cv-analyzer, cv_text_len=2541, job_desc_len=1230
INFO | AgentCore runtime responded in 2350ms
INFO | AgentCore analysis completed successfully. score=82, skills=6
```

**Never logged**:
- CV full text
- AWS credentials
- Personal identifying information

## Troubleshooting

### Issue: `CV_ANALYZER_PROVIDER=agentcore but no runtime configured`

**Cause**: Missing `AGENTCORE_RUNTIME_ID` or `AGENTCORE_RUNTIME_ARN`

**Solution**:
```bash
export AGENTCORE_RUNTIME_ID=your-runtime-id
# OR
export AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:...
```

The system will automatically fall back to SimpleCVAnalyzer if not set.

### Issue: `An error occurred (UnauthorizedOperation) when calling the Invoke operation`

**Cause**: AWS credentials missing or invalid IAM permissions

**Solution**:
1. Verify AWS credentials are set correctly
2. Check IAM role has `bedrock-agentcore:Invoke` permission:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": [
        "bedrock-agentcore:InvokeAgentRuntime"
       ],
       "Resource": "arn:aws:bedrock-agentcore:*:*:runtime/*"
     }]
   }
   ```
3. Verify region matches runtime deployment region

### Issue: `AgentCore response has unexpected structure`

**Cause**: LLM responded with unexpected format

**Solution**:
- Check logs for response content
- Verify LLM model is Claude Sonnet (recommended)
- Try again (LLM responses can vary)

### Issue: Falling back to SimpleCVAnalyzer

**Cause**: AgentCore mode enabled but configuration incomplete

**Solution**:
1. Check logs show: `CV_ANALYZER_PROVIDER=agentcore but no AGENTCORE_RUNTIME_ID...`
2. Set required variables and restart
3. For development, use `CV_ANALYZER_PROVIDER=simple` instead

## Switching Between Modes

### Simple Mode → AgentCore Mode

```bash
# Set environment variables
export CV_ANALYZER_PROVIDER=agentcore
export AGENTCORE_RUNTIME_ID=your-runtime-id
export AWS_REGION=eu-west-1

# Restart backend
docker restart ai-recruitment-backend
# OR
python -m uvicorn app.main:app --reload
```

### AgentCore Mode → Simple Mode

```bash
# Revert to simple
export CV_ANALYZER_PROVIDER=simple

# Restart backend
docker restart ai-recruitment-backend
# OR
python -m uvicorn app.main:app --reload
```

**No code changes required** — the entire architecture is provider-agnostic via the `CVAnalyzer` port.

## Performance Characteristics

### Response Time
- **Mock (SimpleCVAnalyzer)**: ~50-100ms
- **AgentCore**: 1-3 seconds (depends on LLM latency)

### Cost Considerations
- **SimpleCVAnalyzer**: Free (local processing)
- **AgentCore + Claude Sonnet**: Charged per token (typically $0.03-0.06 per analysis)

### Resource Usage
- **SimpleCVAnalyzer**: Minimal CPU
- **AgentCore**: Network I/O, AWS API calls

## Architecture Decisions

### Why boto3 bedrock-agentcore?

We use the low-level boto3 client instead of higher-level SDKs because:
1. **Control**: Full visibility into API calls
2. **Flexibility**: Easy to adjust parameters
3. **Debugging**: Better error handling
4. **Minimal dependencies**: No large inference libraries needed

### Why Direct Claude, Not OpenAI?

1. **Cost**: AWS Bedrock Claude is cheaper for our use case
2. **Data Privacy**: Runs in AWS without external API calls
3. **Integration**: Bedrock AgentCore is AWS-native
4. **Latency**: Same-region AWS calls faster than external APIs

### Why Keep SimpleCVAnalyzer?

1. **Development**: No AWS credentials needed for testing
2. **Fallback**: Graceful degradation if AgentCore unavailable
3. **Cost Control**: Free local analysis option
4. **Testing**: Reliable, deterministic responses for tests

## References

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [claude-cv-analyzer Blueprint](../../cc-swp-blueprint-agent-memory/)
- [CVAnalyzer Port](../app/domain/ports/cv_analyzer.py)
- [AgentCoreClient Implementation](../app/adapters/agent/agentcore_client.py)
- [AgentCoreCVAnalyzer Adapter](../app/adapters/agent/agentcore_cv_analyzer.py)

## Support

For issues or questions:
1. Check logs: `grep "agentcore" backend.log`
2. Review configuration: `echo $CV_ANALYZER_PROVIDER`
3. Test AWS credentials: `aws sts get-caller-identity`
4. Consult this guide or project README

---

**Last Updated**: Sprint 7 of TFG (May 2026)
