"""Project configuration and the secret contract. One directory per project."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from autotester.schema.base import Artifact
from autotester.schema.enums import ProviderRole, SourceKind, WritePolicy


class SecretRef(BaseModel):
    """A declared credential. Holds the KEY and its scope — never the value.

    The value lives only in the repo-root `.env` and is substituted at the
    moment of typing into the browser, scoped to `domains`.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    description: str | None = None
    domains: list[str] = Field(default_factory=list, description="hosts this may be typed into")
    mask_in_screenshot: bool = True

    @field_validator("key")
    @classmethod
    def _reject_value_like(cls, value: str) -> str:
        if len(value) > 64:
            raise ValueError("secret key looks like a value, not a name")
        return value

    @field_validator("domains")
    @classmethod
    def _reject_blank_domains(cls, domains: list[str]) -> list[str]:
        """A blank domain would match an empty host and open the gate (AT-001)."""
        cleaned = [d.strip().lower().lstrip(".") for d in domains]
        if any(not d for d in cleaned):
            raise ValueError("secret domains must be non-empty hostnames")
        return cleaned


class ProviderConfig(BaseModel):
    """Which provider serves each role. Roles are swappable per project."""

    model_config = ConfigDict(extra="forbid")

    vision: str = "gemini"
    agent: str = "langchain-fallback"
    judge: str = "langchain-fallback"

    def for_role(self, role: ProviderRole) -> str:
        return getattr(self, str(role))


class Source(Artifact):
    """An immutable input the system learned from."""

    id: str = ""
    project: str
    kind: SourceKind
    path: str | None = Field(default=None, description="project-relative, for video/doc")
    text: str | None = Field(default=None, description="inline body, for kind=text")
    url: str | None = None
    sha256: str | None = None
    duration_s: float | None = None
    label: str | None = None
    notes: str | None = None

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            from autotester.core.ids import content_id

            key = self.sha256 or self.url or self.text or self.path or self.label
            object.__setattr__(self, "id", content_id("src", {"k": str(self.kind), "v": key}))


class Project(Artifact):
    """Everything the system needs to test one product."""

    slug: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    name: str
    base_url: str
    allowed_domains: list[str] = Field(
        default_factory=list,
        description="the browser may only be driven here; secrets scoped within",
    )
    write_policy: WritePolicy = WritePolicy.READ_ONLY
    secrets: list[SecretRef] = Field(default_factory=list)
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
    headed: bool = Field(default=True, description="real visible browser by default")
    description: str | None = None

    def secret(self, key: str) -> SecretRef | None:
        return next((s for s in self.secrets if s.key == key), None)

    def allows_domain(self, host: str) -> bool:
        """True when `host` is the base host or an allowed domain (or subdomain)."""
        candidates = list(self.allowed_domains)
        return any(host == d or host.endswith(f".{d}") for d in candidates)
