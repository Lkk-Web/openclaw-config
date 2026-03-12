---
name: find-skills
description: >
  Helps users discover and install agent skills when they ask questions like
  "how do I do X", "find a skill for X", "is there a skill that can...", or
  express interest in extending capabilities. This skill should be used when
  the user is looking for functionality that might exist as an installable skill.
metadata:
  origin:
    slug: find-skills
    registry: https://clawhub.ai
    installedVersion: "0.1.0"
    installedAt: 1773282000000
---

# Find Skills

Use this skill when the user asks:
- "how do I do X?" → suggest searching for a skill
- "find a skill for X"
- "is there a skill that can...?"
- "I want to extend my agent to..."

## Workflow

1. **Search ClawHub** using the `clawhub` CLI:
   ```bash
   export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh" && nvm use 20
   clawhub search "<topic>"
   ```

2. **Present results** to the user — show the top 3–5 matches with slug and description.

3. **Install the chosen skill** into the global skills directory:
   ```bash
   clawhub install <slug> --workdir ~/.openclaw/skills --no-input
   ```

4. **Restart the Gateway** so the new skill is loaded:
   ```bash
   openclaw gateway restart
   ```
   Or use the `gateway` tool with `action: "restart"`.

## Tips

- Default install dir for global skills: `~/.openclaw/skills/`
- Per-agent skills go in `~/.openclaw/agents/<agent-id>/workspace/skills/`
- If `clawhub` is not installed: `npm i -g clawhub` (requires Node/nvm)
- If rate-limited, wait ~2 minutes and retry
- Use `clawhub list` to see what's already installed in a workdir

## Common Categories to Search

- `web scraping`, `browser automation`
- `github`, `gitlab`, `gerrit`
- `notion`, `obsidian`, `bear`
- `slack`, `discord`, `telegram`
- `database`, `postgres`, `redis`
- `devops`, `docker`, `kubernetes`
- `image`, `vision`, `ocr`
- `audio`, `tts`, `transcribe`

## Fallback

If no matching skill is found on ClawHub, offer to:
1. Help the user accomplish the task directly with available tools
2. Create a new skill using the `skill-creator` skill
