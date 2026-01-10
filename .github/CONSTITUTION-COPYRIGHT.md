# Copyright Constitution - TrailLensCo Project

## Copyright Policy

**For AI Coding Agents:** See [copilot-instructions.md](copilot-instructions.md) for repository structure and file organization context. This constitution defines copyright header requirements for all source files; copilot-instructions explains which repositories contain which types of files.

**REQUIRED:** All source code files in the TrailLensCo project must include a copyright notice at the top of the file.

## Purpose

- Establish clear ownership of the proprietary codebase
- Protect intellectual property rights
- Explicitly prohibit unauthorized copying, distribution, or use
- Provide legal clarity that this is confidential, proprietary work
- Ensure all contributors understand the private nature of the code

## Scope

This copyright requirement applies to:

- ✅ All source code files (Python, JavaScript, TypeScript, Shell, etc.)
- ✅ Configuration files with executable code
- ✅ SQL scripts and database migration files
- ✅ Build and deployment scripts
- ✅ Documentation with significant original content

This copyright requirement does NOT apply to:

- ❌ Auto-generated files (build outputs, package-lock.json, etc.)
- ❌ Third-party dependencies and libraries
- ❌ Configuration files that are purely data (JSON, YAML without logic)
- ❌ README files and simple markdown documentation
- ❌ License files (LICENSE, COPYING, etc.)

## Copyright Format by File Type

### Python Files

```python
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""Module docstring here."""

import os
import sys
```

### JavaScript/TypeScript Files

```javascript
/**
 * Copyright (c) 2026 TrailLensCo
 * All rights reserved.
 *
 * This file is proprietary and confidential.
 * Unauthorized copying, distribution, or use of this file,
 * via any medium, is strictly prohibited without the express
 * written permission of TrailLensCo.
 */

import React from 'react';
```

### Shell Scripts

```bash
#!/bin/bash
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

set -euo pipefail
```

### Makefile

```makefile
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

.PHONY: all clean
```

### SQL Files

```sql
-- Copyright (c) 2026 TrailLensCo
-- All rights reserved.
--
-- This file is proprietary and confidential.
-- Unauthorized copying, distribution, or use of this file,
-- via any medium, is strictly prohibited without the express
-- written permission of TrailLensCo.

CREATE TABLE users (
  id SERIAL PRIMARY KEY
);
```

### CSS/SCSS Files

```css
/**
 * Copyright (c) 2026 TrailLensCo
 * All rights reserved.
 *
 * This file is proprietary and confidential.
 * Unauthorized copying, distribution, or use of this file,
 * via any medium, is strictly prohibited without the express
 * written permission of TrailLensCo.
 */

.container {
  max-width: 1200px;
}
```

### HTML Files

```html
<!--
Copyright (c) 2026 TrailLensCo
All rights reserved.

This file is proprietary and confidential.
Unauthorized copying, distribution, or use of this file,
via any medium, is strictly prohibited without the express
written permission of TrailLensCo.
-->
<!DOCTYPE html>
<html>
```

## Placement Rules

### Shebang Files

**REQUIRED:** Place copyright immediately after shebang line.

```bash
#!/usr/bin/env python3
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.
```

### Files with Docstrings

**REQUIRED:** Place copyright before module docstring in Python files.

```python
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
Module description here.
"""
```

### JSDoc/TSDoc Files

**REQUIRED:** Place copyright in a separate comment block before any JSDoc.

```typescript
/**
 * Copyright (c) 2026 TrailLensCo
 * All rights reserved.
 *
 * This file is proprietary and confidential.
 * Unauthorized copying, distribution, or use of this file,
 * via any medium, is strictly prohibited without the express
 * written permission of TrailLensCo.
 */

/**
 * @file Component description
 */
```

## Year Guidelines

### New Files

**REQUIRED:** Use the current year when creating new files.

```python
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.
```

### Modified Files

**OPTIONAL:** Update to include range when making substantial changes.

```python
# Copyright (c) 2025-2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.
```

**NOT REQUIRED:** Minor edits (bug fixes, formatting) don't require year updates.

### Multiple Contributors

**For fork/derivative work:**

```python
# Copyright (c) 2026 TrailLensCo
# Portions Copyright (c) 2025 Original Author
```

## Standard Copyright Statement

### Minimum Required Format

```text
Copyright (c) 2026 TrailLensCo
All rights reserved.

This file is proprietary and confidential.
Unauthorized copying, distribution, or use of this file,
via any medium, is strictly prohibited without the express
written permission of TrailLensCo.
```

### Full Format (Recommended)

```text
Copyright (c) 2026 TrailLensCo
All rights reserved.

This file is proprietary and confidential.
Unauthorized copying, distribution, or use of this file,
via any medium, is strictly prohibited without the express
written permission of TrailLensCo.
```

## License Reference

**IMPORTANT:** TrailLensCo source code is **proprietary and confidential**. It is not open source.

The copyright notice explicitly prohibits unauthorized copying, distribution, or use. Additional license terms (if any) may be defined in:

- `/LICENSE` - Primary license file in repository root (if applicable)
- Individual submodule LICENSE files where applicable

**Note:** The copyright notice establishes that this is proprietary work. The notice itself prohibits unauthorized use - no separate license grants permissions unless explicitly provided by TrailLensCo in writing.

## Enforcement

### Pre-commit Checks

**RECOMMENDED:** Implement pre-commit hooks to verify copyright headers.

```bash
#!/bin/bash
# Check for copyright in new files

git diff --cached --name-only --diff-filter=A | while read -r file; do
  if [[ "$file" =~ \.(py|js|ts|sh|tf)$ ]]; then
    if ! head -10 "$file" | grep -q "Copyright.*TrailLensCo"; then
      echo "Missing copyright: $file"
      exit 1
    fi
  fi
done
```

### Automated Tooling

**RECOMMENDED:** Use tools to add/verify copyright headers:

- **Python:** `copyright-header` or custom script
- **JavaScript:** `license-checker`, `addlicense`
- **Multi-language:** `addlicense` tool (Go-based)

```bash
# Install addlicense
go install github.com/google/addlicense@latest

# Add copyright to all files
addlicense -c "TrailLensCo" -y 2026 -l custom .
```

### CI/CD Integration

**RECOMMENDED:** Add copyright verification to CI pipeline:

```yaml
# .github/workflows/copyright-check.yml
name: Copyright Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check copyrights
        run: |
          ./scripts/check-copyright.sh
```

## Exceptions and Waivers

### Third-Party Code

**REQUIRED:** Preserve original copyright for third-party code.

```javascript
/**
 * Copyright (c) 2020 Original Author
 * Licensed under MIT License
 *
 * Modified by TrailLensCo (c) 2026
 */
```

### Template Files

**REQUIRED:** Include copyright but note template status.

```python
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.
#
# Template file - customize as needed
```

### Generated Files

**OPTIONAL:** Add copyright to generator templates, not individual outputs.

## Migration Strategy

### For Existing Codebase

1. **Audit:** Identify files missing copyright headers
2. **Prioritize:** Start with core source files
3. **Automate:** Use tooling to add headers in batch
4. **Review:** Manually verify critical files
5. **Enforce:** Enable pre-commit hooks for new files

### Example Migration Script

```bash
#!/bin/bash
# Add copyright to Python files

find . -name "*.py" -type f | while read -r file; do
  if ! head -5 "$file" | grep -q "Copyright.*TrailLensCo"; then
    cat > "$file.tmp" << 'EOF'
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

EOF
    cat "$file" >> "$file.tmp"
    mv "$file.tmp" "$file"
    echo "Added copyright to: $file"
  fi
done
```

## Best Practices

### DO

- ✅ Add copyright to all new source files immediately
- ✅ Use consistent format across the entire codebase
- ✅ Include license reference for legal clarity
- ✅ Preserve third-party copyrights when integrating external code
- ✅ Automate copyright insertion and verification

### DON'T

- ❌ Mix different copyright formats in the same language
- ❌ Remove or modify third-party copyright notices
- ❌ Add copyright to auto-generated dependency files
- ❌ Use overly verbose or non-standard copyright text
- ❌ Forget to update copyright when forking files

## Repository-Specific Notes

### TrailLensCo Multi-Repository Structure

For the TrailLensCo project with multiple repositories (main, infra, api-dynamo, web, assets):

**REQUIRED:** Each repository maintains its own copyright headers.

**REQUIRED:** Submodule files use "Copyright (c) YEAR TrailLensCo" regardless of which repo they're in.

### Key Repositories

- **`traillensdev/`** - Development workspace (copyright in setup scripts)
- **`infra/`** - Infrastructure code (copyright in all .tf files)
- **`api-dynamo/`** - Backend API (copyright in all .py files)
- **`web/`** - Frontend application (copyright in all .js/.jsx/.ts/.tsx files)
- **`assets/`** - Shared resources (copyright in scripts, not images)

## Summary Checklist

Before committing new code, verify:

- [ ] Copyright header present at top of file
- [ ] Correct year (2026 for new files)
- [ ] Proper comment syntax for file type
- [ ] Shebang appears before copyright (if applicable)
- [ ] Consistent format with existing files
- [ ] License reference included (recommended)
- [ ] Third-party copyrights preserved (if applicable)

## References

- **Canadian Intellectual Property Office:** <https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en>
- **Copyright Best Practices:** <https://opensource.guide/legal/>
- **SPDX License Identifiers:** <https://spdx.org/licenses/>
- **Google Licensing Guide:** <https://opensource.google/documentation/reference/copyright>

---

**Document Status:** Active
**Last Updated:** January 10, 2026
**Applies To:** All source code files in TrailLensCo project
**Authority:** TrailLensCo Legal/Engineering Standards
**Enforcement:** Recommended via pre-commit hooks and CI/CD

