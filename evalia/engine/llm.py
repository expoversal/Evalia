"""Model gateway. Every model call goes through here.

The gateway enforces the engagement's residency policy (it fails closed),
validates structured output against a schema, and caches responses so that a run
can be reproduced. Vendor SDKs are imported only inside this module.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Literal, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

Residency = Literal["us_api", "eu_api", "self_hosted"]
T = TypeVar("T", bound=BaseModel)


class Profile(BaseModel):
    name: str
    provider: Literal["anthropic", "openai_compatible"]
    model: str
    residency: Residency
    region: str
    endpoint: str | None = None
    api_key_env: str


class ResidencyPolicy(BaseModel):
    allowed: list[Residency]


class GatewayError(RuntimeError):
    pass


class ResidencyRefused(GatewayError):
    pass


class ModelUnavailable(GatewayError):
    pass


def load_profiles(path: str | Path) -> dict[str, Profile]:
    """Load profiles from YAML. Values of the form ${NAME} are read from the environment."""
    raw = yaml.safe_load(Path(path).read_text())

    def expand(v):
        if isinstance(v, str):
            return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), v)
        return v

    return {name: Profile(name=name, **{k: expand(v) for k, v in cfg.items()}) for name, cfg in raw["profiles"].items()}


def _first_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return text[start:end + 1]


class Gateway:
    def __init__(self, profile: Profile, policy: ResidencyPolicy, cache_dir: Path):
        if profile.residency not in policy.allowed:
            raise ResidencyRefused(
                f"profile '{profile.name}' processes data as '{profile.residency}', which this engagement does not permit "
                f"(allowed: {', '.join(policy.allowed)})"
            )
        self.profile = profile
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.calls: list[dict] = []

    @property
    def available(self) -> bool:
        return bool(self.profile.model) and bool(os.environ.get(self.profile.api_key_env))

    def _key(self, prompt: str, schema: type[BaseModel]) -> str:
        blob = json.dumps({"provider": self.profile.provider, "model": self.profile.model, "endpoint": self.profile.endpoint,
                           "prompt": prompt, "schema": schema.model_json_schema()}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def _complete(self, prompt: str) -> tuple[str, str]:
        """Send one prompt; return (text, model identifier reported by the provider)."""
        if not self.available:
            raise ModelUnavailable(f"no model or API key configured for profile '{self.profile.name}' "
                                   f"(set EVALIA_MODEL and {self.profile.api_key_env})")
        key = os.environ[self.profile.api_key_env]
        if self.profile.provider == "anthropic":
            import anthropic  # vendor SDK confined to the gateway
            # The endpoint is passed explicitly so that no ambient configuration redirects client data.
            client = anthropic.Anthropic(api_key=key, base_url=self.profile.endpoint or "https://api.anthropic.com")
            # anthropic 2.3.0 exposes no sampling-temperature argument; reproducibility comes from the response cache.
            resp = client.messages.create(model=self.profile.model, max_tokens=4000,
                                          messages=[{"role": "user", "content": prompt}])
            return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text"), resp.model
        if self.profile.provider == "openai_compatible":
            import urllib.request
            req = urllib.request.Request(
                (self.profile.endpoint or "").rstrip("/") + "/chat/completions",
                data=json.dumps({"model": self.profile.model, "temperature": 0,
                                 "messages": [{"role": "user", "content": prompt}]}).encode(),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            return data["choices"][0]["message"]["content"], data.get("model", self.profile.model)
        raise GatewayError(f"unknown provider {self.profile.provider}")

    def structured(self, task: str, prompt: str, schema: type[T]) -> T:
        """Run one task and return output validated against the schema, with one repair attempt."""
        key = self._key(prompt, schema)
        cached = self.cache_dir / f"{key}.json"
        if cached.exists():
            rec = json.loads(cached.read_text())
            self.calls.append({**rec["meta"], "cache_hit": True})
            return schema.model_validate(rec["output"])
        text, model_id = self._complete(prompt)
        try:
            out = schema.model_validate_json(_first_json_object(text))
        except (ValueError, ValidationError) as e:
            repair = (prompt + "\n\nYour previous answer was not valid against the schema. Error:\n" + str(e)[:2000]
                      + "\n\nReturn only the corrected JSON object.")
            text, model_id = self._complete(repair)
            out = schema.model_validate_json(_first_json_object(text))
        meta = {"task": task, "profile": self.profile.name, "provider": self.profile.provider,
                "model_returned": model_id, "region": self.profile.region,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "cache_key": key}
        cached.write_text(json.dumps({"meta": meta, "output": out.model_dump()}, indent=1))
        self.calls.append({**meta, "cache_hit": False})
        return out
