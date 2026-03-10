---
name: skill-vetter
description: "Skill vetting and validation agent. Use when: reviewing, auditing, or validating skills before deployment, ensuring quality and safety standards."
metadata: {"openclaw": {"emoji": "🔍", "requires": {}}}
---

# Skill Vetter

Agent for reviewing and validating skills before deployment.

## When to Use

✅ **USE this skill when:**

- Reviewing new skills before installation
- Auditing existing skills for quality
- Validating skill metadata and structure
- Checking for security issues
- Ensuring AgentSkills spec compliance

## When NOT to Use

❌ **DON'T use this skill when:**

- Creating new skills (use skill-creator instead)
- Simple skill usage questions
- Runtime skill execution

## Core Capabilities

### Structure Validation

- Verify SKILL.md format and frontmatter
- Check required fields (name, description)
- Validate metadata.openclaw structure
- Ensure proper file organization

### Quality Review

- Assess description clarity
- Review usage examples
- Check documentation completeness
- Validate command syntax

### Security Audit

- Identify potential security risks
- Check for unsafe operations
- Review permission requirements
- Validate environment variable usage

### Compliance Check

- Verify AgentSkills spec compliance
- Check OpenClaw-specific requirements
- Validate gating rules (bins, env, config)
- Ensure proper priority handling

## Validation Checklist

### Required Elements
- [ ] Valid YAML frontmatter
- [ ] `name` field present
- [ ] `description` field present
- [ ] Clear usage instructions

### Metadata (if present)
- [ ] Valid JSON in `metadata` field
- [ ] Proper `metadata.openclaw` structure
- [ ] Valid `requires` gating rules
- [ ] Correct `install` specifications

### Documentation
- [ ] "When to Use" section
- [ ] "When NOT to Use" section
- [ ] Clear examples
- [ ] Notes on limitations

### Security
- [ ] No hardcoded secrets
- [ ] Safe command patterns
- [ ] Proper permission handling
- [ ] Clear security implications

## Usage Pattern

1. **Load**: Read SKILL.md file
2. **Parse**: Extract frontmatter and content
3. **Validate**: Check structure and compliance
4. **Audit**: Review for quality and security
5. **Report**: Provide detailed findings

## Notes

- Use before installing third-party skills
- Regular audits for existing skills
- Balance thoroughness with practicality
- Document findings clearly
