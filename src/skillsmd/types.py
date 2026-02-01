"""Type definitions for the skillsmd CLI."""

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Awaitable

# Agent type as a literal union of all supported agent names
AgentType = Literal[
    "amp",
    "antigravity",
    "augment",
    "claude-code",
    "openclaw",
    "cline",
    "codebuddy",
    "codex",
    "command-code",
    "continue",
    "crush",
    "cursor",
    "droid",
    "gemini-cli",
    "github-copilot",
    "goose",
    "iflow-cli",
    "junie",
    "kilo",
    "kimi-cli",
    "kiro-cli",
    "kode",
    "mcpjam",
    "mistral-vibe",
    "mux",
    "neovate",
    "opencode",
    "openhands",
    "pi",
    "qoder",
    "qwen-code",
    "replit",
    "roo",
    "trae",
    "trae-cn",
    "windsurf",
    "zencoder",
    "openclaude",
    "pochi",
    "adal",
]

# List of all valid agent types for iteration
ALL_AGENT_TYPES: list[str] = [
    "amp",
    "antigravity",
    "augment",
    "claude-code",
    "openclaw",
    "cline",
    "codebuddy",
    "codex",
    "command-code",
    "continue",
    "crush",
    "cursor",
    "droid",
    "gemini-cli",
    "github-copilot",
    "goose",
    "iflow-cli",
    "junie",
    "kilo",
    "kimi-cli",
    "kiro-cli",
    "kode",
    "mcpjam",
    "mistral-vibe",
    "mux",
    "neovate",
    "opencode",
    "openhands",
    "pi",
    "qoder",
    "qwen-code",
    "replit",
    "roo",
    "trae",
    "trae-cn",
    "windsurf",
    "zencoder",
    "openclaude",
    "pochi",
    "adal",
]

# Source type for parsed sources
SourceType = Literal["github", "gitlab", "git", "local", "direct-url", "well-known"]

# Install mode
InstallMode = Literal["symlink", "copy"]


@dataclass
class Skill:
    """Represents a skill parsed from SKILL.md."""

    name: str
    description: str
    path: str
    raw_content: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    display_name: str
    skills_dir: str
    global_skills_dir: str | None
    detect_installed: Callable[[], Awaitable[bool]]


@dataclass
class ParsedSource:
    """Parsed source string."""

    type: SourceType
    url: str
    subpath: str | None = None
    local_path: str | None = None
    ref: str | None = None
    skill_filter: str | None = None


@dataclass
class RemoteSkill:
    """Represents a skill fetched from a remote host provider."""

    name: str
    description: str
    content: str
    install_name: str
    source_url: str
    provider_id: str
    source_identifier: str
    metadata: dict[str, Any] | None = None


@dataclass
class InstallResult:
    """Result of a skill installation."""

    success: bool
    path: str
    mode: InstallMode
    canonical_path: str | None = None
    symlink_failed: bool = False
    error: str | None = None


@dataclass
class InstalledSkill:
    """Information about an installed skill."""

    name: str
    description: str
    path: str
    canonical_path: str
    scope: Literal["project", "global"]
    agents: list[str] = field(default_factory=list)
