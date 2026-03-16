"""AWS Bedrock Backend - IAM role / STS / access key auth. Never hardcode secrets."""
from __future__ import annotations
import json
import asyncio
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import LLMClient
from ..config import settings


class BedrockClient(LLMClient):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self._client = None
        self._model = self.config.get("model", settings.bedrock_model)
        self._region = self.config.get("region", settings.bedrock_region)
        logger.info(f"[Bedrock] region={self._region} model={self._model}")

    def _get_client(self):
        if self._client:
            return self._client
        import boto3
        kwargs = {"region_name": self._region}
        
        role_arn = self.config.get("role_arn", settings.bedrock_role_arn)
        access_key = self.config.get("aws_access_key_id", settings.aws_access_key_id)
        secret_key = self.config.get("aws_secret_access_key", settings.aws_secret_access_key)
        session_token = self.config.get("aws_session_token", settings.aws_session_token)

        if role_arn:
            # Assume IAM role via STS
            sts = boto3.client("sts", region_name=self._region)
            role = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName="prism-ai-bedrock"
            )
            creds = role["Credentials"]
            kwargs.update({
                "aws_access_key_id": creds["AccessKeyId"],
                "aws_secret_access_key": creds["SecretAccessKey"],
                "aws_session_token": creds["SessionToken"],
            })
        elif access_key:
            kwargs.update({
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
            })
            if session_token:
                kwargs["aws_session_token"] = session_token
        
        self._client = boto3.client("bedrock-runtime", **kwargs)
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        client = self._get_client()
        model_id = self._model
        max_tokens = self.config.get("max_tokens", settings.llm_max_tokens)
        temperature = self.config.get("temperature", settings.llm_temperature)
        
        # Claude models use Messages API
        if "anthropic" in model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                body["system"] = system
        else:
            # Fallback for Titan / Llama
            body = {"inputText": f"{system}\n{prompt}" if system else prompt,
                    "textGenerationConfig": {"maxTokenCount": max_tokens, "temperature": temperature}}
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
        )
        resp_body = json.loads(response["body"].read())
        if "anthropic" in model_id:
            result = resp_body["content"][0]["text"].strip()
        else:
            result = resp_body.get("results", [{}])[0].get("outputText", "").strip()
        logger.debug(f"[Bedrock] response length={len(result)}")
        return result

    async def list_models(self) -> list[str]:
        return [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "amazon.titan-text-premier-v1:0",
            "meta.llama3-70b-instruct-v1:0",
        ]

    async def health_check(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception as e:
            logger.warning(f"[Bedrock] health_check failed: {e}")
            return False
