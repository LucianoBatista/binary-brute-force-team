# binary-brute-force-team
Assistant that creates interactive images for STEM use cases

## Quick Start

```bash
# Start all services
docker compose up -d

# Access the application
open http://localhost:8010
```

## Validation Scripts

Standalone scripts for testing workflows before route integration.

### Educational Workflow Validation

Test the multi-agent educational workflow with a markdown file containing PDF text:

```bash
# Basic usage
uv run scripts/validate_educational_workflow.py \
  --input scripts/input/sample.md \
  --query "Create a visualization of the Pythagorean theorem"

# Use query from markdown frontmatter
uv run scripts/validate_educational_workflow.py \
  --input scripts/input/sample.md

# With verbose logging
uv run scripts/validate_educational_workflow.py \
  --input scripts/input/sample.md \
  --verbose
```

**Input format** (`scripts/input/sample.md`):
```markdown
---
query: "Create a visualization explaining the concept"
---

# PDF Content Here

Your extracted PDF text goes here...
```

**Outputs** (in `scripts/output/`):
- `result.json` - Full workflow result
- `manim_code.py` - Generated Manim code
- `media/` - Generated images/videos (PNG/MP4)
- `logs/` - Timestamped execution logs

## Documentation

See [CLAUDE.md](CLAUDE.md) for full project documentation including:
- Architecture overview
- API endpoints
- Docker setup
- Development guide
