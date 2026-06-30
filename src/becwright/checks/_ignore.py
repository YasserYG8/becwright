from __future__ import annotations

import re

# A line carrying this marker (inside a comment, in any language) is exempt from
# any check: `# becwright: ignore`, `// becwright: ignore`, etc.
_MARKER = re.compile(r"becwright:\s*ignore\b", re.IGNORECASE)


def is_ignored(line: str) -> bool:
    return bool(_MARKER.search(line))
