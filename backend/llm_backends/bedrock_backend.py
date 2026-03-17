from .base import LLMClient
from ..config import get_settings
import json


class BedrockBackend(LLMClient):
    def __init__(self):
        settings = get_settings()
        self.region = settings.bedrock_region
        self.model_id = settings.bedrock_model

        try:
            import boto3
            session_kwargs = {"region_name": self.region}

            if settings.bedrock_access_key and settings.bedrock_secret_key:
                session_kwargs["aws_access_key_id"] = settings.bedrock_access_key
                session_kwargs["aws_secret_access_key"] = settings.bedrock_secret_key

            if settings.bedrock_role_arn:
                sts = boto3.client("sts", **session_kwargs)
                assumed_role = sts.assume_role(
                    RoleArn=settings.bedrock_role_arn,
                    RoleSessionName="prism-ai-session"
                )
                credentials = assumed_role["Credentials"]
                session_kwargs = {
                    "region_name": self.region,
                    "aws_access_key_id": credentials["AccessKeyId"],
                    "aws_secret_access_key": credentials["SecretAccessKey"],
                    "aws_session_token": credentials["SessionToken"],
                }

            self.client = boto3.client("bedrock-runtime", **session_kwargs)
        except ImportError:
            raise RuntimeError("boto3 not installed. Run: pip install boto3")

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
        try:
            if "claude" in self.model_id.lower():
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                })
            elif "titan" in self.model_id.lower():
                body = json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "temperature": temperature,
                        "maxTokenCount": max_tokens,
                    }
                })
            else:
                body = json.dumps({
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                })

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )

            response_body = json.loads(response["body"].read())

            if "claude" in self.model_id.lower():
                return response_body["content"][0]["text"]
            elif "titan" in self.model_id.lower():
                return response_body["results"][0]["outputText"]
            else:
                return response_body.get("completion", response_body.get("text", ""))

        except Exception as e:
            raise RuntimeError(f"Bedrock generation failed: {e}")

    async def health_check(self) -> bool:
        try:
            self.client.list_foundation_models()
            return True
        except:
            return False

    def get_model_name(self) -> str:
        return self.model_id
