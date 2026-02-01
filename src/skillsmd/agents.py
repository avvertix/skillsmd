"""Agent configurations for the skillsmd CLI."""

import os
from pathlib import Path

from skillsmd.types import AgentConfig, ALL_AGENT_TYPES


def _get_home() -> Path:
    """Get the user's home directory."""
    return Path.home()


def _get_config_home() -> Path:
    """Get the XDG config home directory."""
    xdg_config = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config:
        return Path(xdg_config)
    return _get_home() / '.config'


def _get_codex_home() -> Path:
    """Get the Codex home directory."""
    codex_home = os.environ.get('CODEX_HOME', '').strip()
    if codex_home:
        return Path(codex_home)
    return _get_home() / '.codex'


def _get_claude_home() -> Path:
    """Get the Claude home directory."""
    claude_home = os.environ.get('CLAUDE_CONFIG_DIR', '').strip()
    if claude_home:
        return Path(claude_home)
    return _get_home() / '.claude'


def _get_openclaw_global_dir() -> Path:
    """Get the OpenClaw global skills directory."""
    home = _get_home()
    if (home / '.openclaw').exists():
        return home / '.openclaw' / 'skills'
    if (home / '.clawdbot').exists():
        return home / '.clawdbot' / 'skills'
    return home / '.moltbot' / 'skills'


# Cache for agent configs
_agents_cache: dict[str, AgentConfig] | None = None


def _build_agents() -> dict[str, AgentConfig]:
    """Build the agent configurations dictionary."""
    home = _get_home()
    config_home = _get_config_home()
    codex_home = _get_codex_home()
    claude_home = _get_claude_home()

    return {
        'amp': AgentConfig(
            name='amp',
            display_name='Amp',
            skills_dir='.agents/skills',
            global_skills_dir=str(config_home / 'agents' / 'skills'),
            detect_installed=lambda: _async_exists(config_home / 'amp'),
        ),
        'antigravity': AgentConfig(
            name='antigravity',
            display_name='Antigravity',
            skills_dir='.agent/skills',
            global_skills_dir=str(home / '.gemini' / 'antigravity' / 'global_skills'),
            detect_installed=lambda: _async_any_exists(
                Path.cwd() / '.agent', home / '.gemini' / 'antigravity'
            ),
        ),
        'augment': AgentConfig(
            name='augment',
            display_name='Augment',
            skills_dir='.augment/rules',
            global_skills_dir=str(home / '.augment' / 'rules'),
            detect_installed=lambda: _async_exists(home / '.augment'),
        ),
        'claude-code': AgentConfig(
            name='claude-code',
            display_name='Claude Code',
            skills_dir='.claude/skills',
            global_skills_dir=str(claude_home / 'skills'),
            detect_installed=lambda: _async_exists(claude_home),
        ),
        'openclaw': AgentConfig(
            name='openclaw',
            display_name='OpenClaw',
            skills_dir='skills',
            global_skills_dir=str(_get_openclaw_global_dir()),
            detect_installed=lambda: _async_any_exists(
                home / '.openclaw', home / '.clawdbot', home / '.moltbot'
            ),
        ),
        'cline': AgentConfig(
            name='cline',
            display_name='Cline',
            skills_dir='.cline/skills',
            global_skills_dir=str(home / '.cline' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.cline'),
        ),
        'codebuddy': AgentConfig(
            name='codebuddy',
            display_name='CodeBuddy',
            skills_dir='.codebuddy/skills',
            global_skills_dir=str(home / '.codebuddy' / 'skills'),
            detect_installed=lambda: _async_any_exists(
                Path.cwd() / '.codebuddy', home / '.codebuddy'
            ),
        ),
        'codex': AgentConfig(
            name='codex',
            display_name='Codex',
            skills_dir='.codex/skills',
            global_skills_dir=str(codex_home / 'skills'),
            detect_installed=lambda: _async_any_exists(codex_home, Path('/etc/codex')),
        ),
        'command-code': AgentConfig(
            name='command-code',
            display_name='Command Code',
            skills_dir='.commandcode/skills',
            global_skills_dir=str(home / '.commandcode' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.commandcode'),
        ),
        'continue': AgentConfig(
            name='continue',
            display_name='Continue',
            skills_dir='.continue/skills',
            global_skills_dir=str(home / '.continue' / 'skills'),
            detect_installed=lambda: _async_any_exists(
                Path.cwd() / '.continue', home / '.continue'
            ),
        ),
        'crush': AgentConfig(
            name='crush',
            display_name='Crush',
            skills_dir='.crush/skills',
            global_skills_dir=str(home / '.config' / 'crush' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.config' / 'crush'),
        ),
        'cursor': AgentConfig(
            name='cursor',
            display_name='Cursor',
            skills_dir='.cursor/skills',
            global_skills_dir=str(home / '.cursor' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.cursor'),
        ),
        'droid': AgentConfig(
            name='droid',
            display_name='Droid',
            skills_dir='.factory/skills',
            global_skills_dir=str(home / '.factory' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.factory'),
        ),
        'gemini-cli': AgentConfig(
            name='gemini-cli',
            display_name='Gemini CLI',
            skills_dir='.gemini/skills',
            global_skills_dir=str(home / '.gemini' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.gemini'),
        ),
        'github-copilot': AgentConfig(
            name='github-copilot',
            display_name='GitHub Copilot',
            skills_dir='.github/skills',
            global_skills_dir=str(home / '.copilot' / 'skills'),
            detect_installed=lambda: _async_any_exists(
                Path.cwd() / '.github', home / '.copilot'
            ),
        ),
        'goose': AgentConfig(
            name='goose',
            display_name='Goose',
            skills_dir='.goose/skills',
            global_skills_dir=str(config_home / 'goose' / 'skills'),
            detect_installed=lambda: _async_exists(config_home / 'goose'),
        ),
        'junie': AgentConfig(
            name='junie',
            display_name='Junie',
            skills_dir='.junie/skills',
            global_skills_dir=str(home / '.junie' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.junie'),
        ),
        'iflow-cli': AgentConfig(
            name='iflow-cli',
            display_name='iFlow CLI',
            skills_dir='.iflow/skills',
            global_skills_dir=str(home / '.iflow' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.iflow'),
        ),
        'kilo': AgentConfig(
            name='kilo',
            display_name='Kilo Code',
            skills_dir='.kilocode/skills',
            global_skills_dir=str(home / '.kilocode' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.kilocode'),
        ),
        'kimi-cli': AgentConfig(
            name='kimi-cli',
            display_name='Kimi Code CLI',
            skills_dir='.agents/skills',
            global_skills_dir=str(home / '.config' / 'agents' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.kimi'),
        ),
        'kiro-cli': AgentConfig(
            name='kiro-cli',
            display_name='Kiro CLI',
            skills_dir='.kiro/skills',
            global_skills_dir=str(home / '.kiro' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.kiro'),
        ),
        'kode': AgentConfig(
            name='kode',
            display_name='Kode',
            skills_dir='.kode/skills',
            global_skills_dir=str(home / '.kode' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.kode'),
        ),
        'mcpjam': AgentConfig(
            name='mcpjam',
            display_name='MCPJam',
            skills_dir='.mcpjam/skills',
            global_skills_dir=str(home / '.mcpjam' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.mcpjam'),
        ),
        'mistral-vibe': AgentConfig(
            name='mistral-vibe',
            display_name='Mistral Vibe',
            skills_dir='.vibe/skills',
            global_skills_dir=str(home / '.vibe' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.vibe'),
        ),
        'mux': AgentConfig(
            name='mux',
            display_name='Mux',
            skills_dir='.mux/skills',
            global_skills_dir=str(home / '.mux' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.mux'),
        ),
        'opencode': AgentConfig(
            name='opencode',
            display_name='OpenCode',
            skills_dir='.opencode/skills',
            global_skills_dir=str(config_home / 'opencode' / 'skills'),
            detect_installed=lambda: _async_any_exists(
                config_home / 'opencode', claude_home / 'skills'
            ),
        ),
        'openclaude': AgentConfig(
            name='openclaude',
            display_name='OpenClaude IDE',
            skills_dir='.openclaude/skills',
            global_skills_dir=str(home / '.openclaude' / 'skills'),
            detect_installed=lambda: _async_any_exists(
                home / '.openclaude', Path.cwd() / '.openclaude'
            ),
        ),
        'openhands': AgentConfig(
            name='openhands',
            display_name='OpenHands',
            skills_dir='.openhands/skills',
            global_skills_dir=str(home / '.openhands' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.openhands'),
        ),
        'pi': AgentConfig(
            name='pi',
            display_name='Pi',
            skills_dir='.pi/skills',
            global_skills_dir=str(home / '.pi' / 'agent' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.pi' / 'agent'),
        ),
        'qoder': AgentConfig(
            name='qoder',
            display_name='Qoder',
            skills_dir='.qoder/skills',
            global_skills_dir=str(home / '.qoder' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.qoder'),
        ),
        'qwen-code': AgentConfig(
            name='qwen-code',
            display_name='Qwen Code',
            skills_dir='.qwen/skills',
            global_skills_dir=str(home / '.qwen' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.qwen'),
        ),
        'replit': AgentConfig(
            name='replit',
            display_name='Replit',
            skills_dir='.agent/skills',
            global_skills_dir=None,
            detect_installed=lambda: _async_exists(Path.cwd() / '.agent'),
        ),
        'roo': AgentConfig(
            name='roo',
            display_name='Roo Code',
            skills_dir='.roo/skills',
            global_skills_dir=str(home / '.roo' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.roo'),
        ),
        'trae': AgentConfig(
            name='trae',
            display_name='Trae',
            skills_dir='.trae/skills',
            global_skills_dir=str(home / '.trae' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.trae'),
        ),
        'trae-cn': AgentConfig(
            name='trae-cn',
            display_name='Trae CN',
            skills_dir='.trae/skills',
            global_skills_dir=str(home / '.trae-cn' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.trae-cn'),
        ),
        'windsurf': AgentConfig(
            name='windsurf',
            display_name='Windsurf',
            skills_dir='.windsurf/skills',
            global_skills_dir=str(home / '.codeium' / 'windsurf' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.codeium' / 'windsurf'),
        ),
        'zencoder': AgentConfig(
            name='zencoder',
            display_name='Zencoder',
            skills_dir='.zencoder/skills',
            global_skills_dir=str(home / '.zencoder' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.zencoder'),
        ),
        'neovate': AgentConfig(
            name='neovate',
            display_name='Neovate',
            skills_dir='.neovate/skills',
            global_skills_dir=str(home / '.neovate' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.neovate'),
        ),
        'pochi': AgentConfig(
            name='pochi',
            display_name='Pochi',
            skills_dir='.pochi/skills',
            global_skills_dir=str(home / '.pochi' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.pochi'),
        ),
        'adal': AgentConfig(
            name='adal',
            display_name='AdaL',
            skills_dir='.adal/skills',
            global_skills_dir=str(home / '.adal' / 'skills'),
            detect_installed=lambda: _async_exists(home / '.adal'),
        ),
    }


async def _async_exists(path: Path) -> bool:
    """Check if a path exists (async wrapper)."""
    return path.exists()


async def _async_any_exists(*paths: Path) -> bool:
    """Check if any of the paths exist (async wrapper)."""
    return any(p.exists() for p in paths)


def get_agents() -> dict[str, AgentConfig]:
    """Get all agent configurations."""
    global _agents_cache
    if _agents_cache is None:
        _agents_cache = _build_agents()
    return _agents_cache


def get_agent_config(agent_type: str) -> AgentConfig:
    """Get configuration for a specific agent."""
    agents = get_agents()
    if agent_type not in agents:
        raise ValueError(f'Unknown agent type: {agent_type}')
    return agents[agent_type]


async def detect_installed_agents() -> list[str]:
    """Detect which agents are installed on the system."""
    agents = get_agents()
    installed: list[str] = []

    for agent_type in ALL_AGENT_TYPES:
        config = agents.get(agent_type)
        if config and await config.detect_installed():
            installed.append(agent_type)

    return installed
