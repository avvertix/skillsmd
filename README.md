# skillsmd

Python CLI for using [agent skills](https://agentskills.io/home). 

Supports **OpenCode**, **Claude Code**, **Codex**, **Cursor**, and [36 more](#supported-agents).

**It is a port of [Vercel Skills](https://github.com/vercel-labs/skills) to Python**. Commands that search for skills do that on Vercel [skills.sh](https://skills.sh/).

## Install a Skill

```bash
uvx skillsmd add vercel-labs/agent-skills
```

### Source Formats

```bash
# GitHub shorthand (owner/repo)
uvx skillsmd add vercel-labs/agent-skills

# Full GitHub URL
uvx skillsmd add https://github.com/vercel-labs/agent-skills

# Direct path to a skill in a repo
uvx skillsmd add https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines

# GitLab URL
uvx skillsmd add https://gitlab.com/org/repo

# Any git URL
uvx skillsmd add git@github.com:vercel-labs/agent-skills.git

# Local path
uvx skillsmd add ./my-local-skills
```

### Options

| Option                    | Description                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------- |
| `-g, --global`            | Install to user directory instead of project                                                      |
| `-a, --agent <agents...>` | Target specific agents (e.g., `claude-code`, `codex`). See [Supported Agents](#supported-agents)  |
| `-s, --skill <skills...>` | Install specific skills by name (use `'*'` for all skills)                                        |
| `-l, --list`              | List available skills without installing                                                          |
| `-y, --yes`               | Skip all confirmation prompts                                                                     |
| `--all`                   | Install all skills to all agents without prompts                                                  |

### Examples

```bash
# List skills in a repository
uvx skillsmd add vercel-labs/agent-skills --list

# Install specific skills
uvx skillsmd add vercel-labs/agent-skills --skill frontend-design --skill skill-creator

# Install a skill with spaces in the name (must be quoted)
uvx skillsmd add owner/repo --skill "Convex Best Practices"

# Install to specific agents
uvx skillsmd add vercel-labs/agent-skills -a claude-code -a opencode

# Non-interactive installation (CI/CD friendly)
uvx skillsmd add vercel-labs/agent-skills --skill frontend-design -g -a claude-code -y

# Install all skills from a repo to all agents
uvx skillsmd add vercel-labs/agent-skills --all

# Install all skills to specific agents
uvx skillsmd add vercel-labs/agent-skills --skill '*' -a claude-code

# Install specific skills to all agents
uvx skillsmd add vercel-labs/agent-skills --agent '*' --skill frontend-design
```

### Installation Scope

| Scope       | Flag      | Location            | Use Case                                      |
| ----------- | --------- | ------------------- | --------------------------------------------- |
| **Project** | (default) | `./<agent>/skills/` | Committed with your project, shared with team |
| **Global**  | `-g`      | `~/<agent>/skills/` | Available across all projects                 |

### Installation Methods

When installing interactively, you can choose:

| Method                    | Description                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------- |
| **Symlink** (Recommended) | Creates symlinks from each agent to a canonical copy. Single source of truth, easy updates. |
| **Copy**                  | Creates independent copies for each agent. Use when symlinks aren't supported.              |

## Other Commands

| Command                      | Description                                             |
| ---------------------------- | ------------------------------------------------------- |
| `uvx skillsmd list`            | List installed skills (alias: `ls`)                     |
| `uvx skillsmd find [query]`    | Search for skills interactively or by keyword           |
| `uvx skillsmd remove [skills]` | Remove installed skills from agents                     |
| `uvx skillsmd check`           | Check for available skill updates                       |
| `uvx skillsmd update`          | Update all installed skills to latest versions          |
| `uvx skillsmd init [name]`     | Create a new SKILL.md template                          |

### `skills list`

List all installed skills. Similar to `npm ls`.

```bash
# List all installed skills (project and global)
uvx skillsmd list

# List only global skills
uvx skillsmd ls -g

# Filter by specific agents
uvx skillsmd ls -a claude-code -a cursor
```

### `skills find`

Search for skills interactively or by keyword.

```bash
# Interactive search (fzf-style)
uvx skillsmd find

# Search by keyword
uvx skillsmd find pdf
```

### `skills check` / `skills update`

```bash
# Check if any installed skills have updates
uvx skillsmd check

# Update all skills to latest versions
uvx skillsmd update
```

### `skills init`

```bash
# Create SKILL.md in current directory
uvx skillsmd init

# Create a new skill in a subdirectory
uvx skillsmd init my-skill
```

### `skills remove`

Remove installed skills from agents.

```bash
# Remove interactively (select from installed skills)
uvx skillsmd remove

# Remove specific skill by name
uvx skillsmd remove web-design-guidelines

# Remove multiple skills
uvx skillsmd remove frontend-design web-design-guidelines

# Remove from global scope
uvx skillsmd remove --global web-design-guidelines

# Remove from specific agents only
uvx skillsmd remove --agent claude-code cursor my-skill

# Remove all installed skills without confirmation
uvx skillsmd remove --all

# Remove all skills from a specific agent
uvx skillsmd remove --skill '*' -a cursor

# Remove a specific skill from all agents
uvx skillsmd remove my-skill --agent '*'

# Use 'rm' alias
uvx skillsmd rm my-skill
```

| Option              | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `-g, --global`      | Remove from global scope (~/) instead of project      |
| `-a, --agent`       | Remove from specific agents (use `'*'` for all)      |
| `-s, --skill`       | Specify skills to remove (use `'*'` for all)         |
| `-y, --yes`         | Skip confirmation prompts                            |
| `--all`             | Shorthand for `--skill '*' --agent '*' -y`           |

## What are Agent Skills?

Agent skills are reusable instruction sets for coding agents, defined in `SKILL.md` files with YAML frontmatter containing a `name` and `description`.

Skills let agents perform tasks like:

- Generating release notes from git history
- Creating PRs following your team's conventions
- Integrating with external tools (Linear, Notion, etc.)

Discover skills at **[skills.sh](https://skills.sh)**

## Supported Agents

Skills can be installed to any of these agents:

| Agent | `--agent` | Project Path | Global Path |
|-------|-----------|--------------|-------------|
| Amp, Kimi Code CLI | `amp`, `kimi-cli` | `.agents/skills/` | `~/.config/agents/skills/` |
| Antigravity | `antigravity` | `.agent/skills/` | `~/.gemini/antigravity/global_skills/` |
| Augment | `augment` | `.augment/rules/` | `~/.augment/rules/` |
| Claude Code | `claude-code` | `.claude/skills/` | `~/.claude/skills/` |
| OpenClaw | `openclaw` | `skills/` | `~/.moltbot/skills/` |
| Cline | `cline` | `.cline/skills/` | `~/.cline/skills/` |
| CodeBuddy | `codebuddy` | `.codebuddy/skills/` | `~/.codebuddy/skills/` |
| Codex | `codex` | `.codex/skills/` | `~/.codex/skills/` |
| Command Code | `command-code` | `.commandcode/skills/` | `~/.commandcode/skills/` |
| Continue | `continue` | `.continue/skills/` | `~/.continue/skills/` |
| Crush | `crush` | `.crush/skills/` | `~/.config/crush/skills/` |
| Cursor | `cursor` | `.cursor/skills/` | `~/.cursor/skills/` |
| Droid | `droid` | `.factory/skills/` | `~/.factory/skills/` |
| Gemini CLI | `gemini-cli` | `.gemini/skills/` | `~/.gemini/skills/` |
| GitHub Copilot | `github-copilot` | `.github/skills/` | `~/.copilot/skills/` |
| Goose | `goose` | `.goose/skills/` | `~/.config/goose/skills/` |
| Junie | `junie` | `.junie/skills/` | `~/.junie/skills/` |
| iFlow CLI | `iflow-cli` | `.iflow/skills/` | `~/.iflow/skills/` |
| Kilo Code | `kilo` | `.kilocode/skills/` | `~/.kilocode/skills/` |
| Kiro CLI | `kiro-cli` | `.kiro/skills/` | `~/.kiro/skills/` |
| Kode | `kode` | `.kode/skills/` | `~/.kode/skills/` |
| MCPJam | `mcpjam` | `.mcpjam/skills/` | `~/.mcpjam/skills/` |
| Mistral Vibe | `mistral-vibe` | `.vibe/skills/` | `~/.vibe/skills/` |
| Mux | `mux` | `.mux/skills/` | `~/.mux/skills/` |
| OpenCode | `opencode` | `.opencode/skills/` | `~/.config/opencode/skills/` |
| OpenClaude IDE | `openclaude` | `.openclaude/skills/` | `~/.openclaude/skills/` |
| OpenHands | `openhands` | `.openhands/skills/` | `~/.openhands/skills/` |
| Pi | `pi` | `.pi/skills/` | `~/.pi/agent/skills/` |
| Qoder | `qoder` | `.qoder/skills/` | `~/.qoder/skills/` |
| Qwen Code | `qwen-code` | `.qwen/skills/` | `~/.qwen/skills/` |
| Replit | `replit` | `.agent/skills/` | N/A (project-only) |
| Roo Code | `roo` | `.roo/skills/` | `~/.roo/skills/` |
| Trae | `trae` | `.trae/skills/` | `~/.trae/skills/` |
| Trae CN | `trae-cn` | `.trae/skills/` | `~/.trae-cn/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |
| Zencoder | `zencoder` | `.zencoder/skills/` | `~/.zencoder/skills/` |
| Neovate | `neovate` | `.neovate/skills/` | `~/.neovate/skills/` |
| Pochi | `pochi` | `.pochi/skills/` | `~/.pochi/skills/` |
| AdaL | `adal` | `.adal/skills/` | `~/.adal/skills/` |

> [!NOTE]
> **Kiro CLI users:** After installing skills, manually add them to your custom agent's `resources` in
> `.kiro/agents/<agent>.json`:
>
> ```json
> {
>   "resources": ["skill://.kiro/skills/**/SKILL.md"]
> }
> ```

The CLI automatically detects which coding agents you have installed. If none are detected, you'll be prompted to select
which agents to install to.

## Creating Skills

Skills are directories containing a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: my-skill
description: What this skill does and when to use it
---

# My Skill

Instructions for the agent to follow when this skill is activated.

## When to Use

Describe the scenarios where this skill should be used.

## Steps

1. First, do this
2. Then, do that
```

### Required Fields

- `name`: Unique identifier (lowercase, hyphens allowed)
- `description`: Brief explanation of what the skill does

### Optional Fields

- `metadata.internal`: Set to `true` to hide the skill from normal discovery. Internal skills are only visible and
  installable when `INSTALL_INTERNAL_SKILLS=1` is set. Useful for work-in-progress skills or skills meant only for
  internal tooling.

```markdown
---
name: my-internal-skill
description: An internal skill not shown by default
metadata:
  internal: true
---
```

### Skill Discovery

The CLI searches for skills in these locations within a repository:

- Root directory (if it contains `SKILL.md`)
- `skills/`
- `skills/.curated/`
- `skills/.experimental/`
- `skills/.system/`
- `.agents/skills/`
- `.agent/skills/`
- `.augment/rules/`
- `.claude/skills/`
- `./skills/`
- `.cline/skills/`
- `.codebuddy/skills/`
- `.codex/skills/`
- `.commandcode/skills/`
- `.continue/skills/`
- `.crush/skills/`
- `.cursor/skills/`
- `.factory/skills/`
- `.gemini/skills/`
- `.github/skills/`
- `.goose/skills/`
- `.junie/skills/`
- `.iflow/skills/`
- `.kilocode/skills/`
- `.kiro/skills/`
- `.kode/skills/`
- `.mcpjam/skills/`
- `.vibe/skills/`
- `.mux/skills/`
- `.opencode/skills/`
- `.openclaude/skills/`
- `.openhands/skills/`
- `.pi/skills/`
- `.qoder/skills/`
- `.qwen/skills/`
- `.roo/skills/`
- `.trae/skills/`
- `.windsurf/skills/`
- `.zencoder/skills/`
- `.neovate/skills/`
- `.pochi/skills/`
- `.adal/skills/`

If no skills are found in standard locations, a recursive search is performed.

## Compatibility

Skills are generally compatible across agents since they follow a shared [Agent Skills specification](https://agentskills.io). Some features may be agent-specific.

## Troubleshooting

### "No skills found"

Ensure the repository contains valid `SKILL.md` files with both `name` and `description` in the frontmatter.

### Skill not loading in agent

- Verify the skill was installed to the correct path
- Restart the agent, if running in cli
- Check the agent's documentation for skill loading requirements
- Ensure the `SKILL.md` frontmatter is valid YAML

### Permission errors

Ensure you have write access to the target directory.

## Environment Variables

| Variable                  | Description                                                                |
| ------------------------- | -------------------------------------------------------------------------- |
| `INSTALL_INTERNAL_SKILLS` | Set to `1` or `true` to show and install skills marked as `internal: true` |

```bash
# Install internal skills
INSTALL_INTERNAL_SKILLS=1 uvx skillsmd add vercel-labs/agent-skills --list
```


## Related Links

- [Agent Skills Specification](https://agentskills.io)
- [Skills Directory](https://skills.sh)
- [Amp Skills Documentation](https://ampcode.com/manual#agent-skills)
- [Antigravity Skills Documentation](https://antigravity.google/docs/skills)
- [Factory AI / Droid Skills Documentation](https://docs.factory.ai/cli/configuration/skills)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Clawdbot Skills Documentation](https://docs.clawd.bot/tools/skills)
- [Cline Skills Documentation](https://docs.cline.bot/features/skills)
- [CodeBuddy Skills Documentation](https://www.codebuddy.ai/docs/ide/Features/Skills)
- [Codex Skills Documentation](https://developers.openai.com/codex/skills)
- [Command Code Skills Documentation](https://commandcode.ai/docs/skills)
- [Crush Skills Documentation](https://github.com/charmbracelet/crush?tab=readme-ov-file#agent-skills)
- [Cursor Skills Documentation](https://cursor.com/docs/context/skills)
- [Gemini CLI Skills Documentation](https://geminicli.com/docs/cli/skills/)
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [iFlow CLI Skills Documentation](https://platform.iflow.cn/en/cli/examples/skill)
- [Kimi Code CLI Skills Documentation](https://moonshotai.github.io/kimi-cli/en/customization/skills.html)
- [Kiro CLI Skills Documentation](https://kiro.dev/docs/cli/custom-agents/configuration-reference/#skill-resources)
- [Kode Skills Documentation](https://github.com/shareAI-lab/kode/blob/main/docs/skills.md)
- [OpenCode Skills Documentation](https://opencode.ai/docs/skills)
- [Qwen Code Skills Documentation](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/)
- [OpenHands Skills Documentation](https://docs.openhands.ai/modules/usage/how-to/using-skills)
- [Pi Skills Documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md)
- [Qoder Skills Documentation](https://docs.qoder.com/cli/Skills)
- [Replit Skills Documentation](https://docs.replit.com/replitai/skills)
- [Roo Code Skills Documentation](https://docs.roocode.com/features/skills)
- [Trae Skills Documentation](https://docs.trae.ai/ide/skills)
- [Vercel Agent Skills Repository](https://github.com/vercel-labs/agent-skills)

## License

MIT
