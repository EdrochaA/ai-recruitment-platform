# ai-recruitment-agentcore-runtime

Minimal AgentCore Runtime for CV analysis. This is a separate runtime component
from the FastAPI backend and is intended to be deployed to AWS Bedrock
AgentCore Runtime.

## Local test

```bash
python app.py
```

The script prints a mock JSON response for a sample payload.

## Payload contract

Input JSON:
```
{
  "cv_text": "...",
  "job_offer": "..."  // optional (alias: job_description)
}
```

Output JSON:
```
{
  "score": 0,
  "summary": "...",
  "skills": ["python", "fastapi"],
  "experience": "...",
  "experience_summary": "..."
}
```

The `experience_summary` field is included to keep compatibility with the
backend `CVAnalysisResult` contract.
