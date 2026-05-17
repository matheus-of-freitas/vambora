#!/usr/bin/env bash
# Fails if feature code reaches for raw colors or arbitrary Tailwind values.
# Token-only is the rule (see plan and docs/development/conventions.md "Design system").
#
# Allowed exceptions (matched by path):
#   - src/app/globals.css            -- token definitions
#   - tailwind.config.ts             -- token references
#   - src/shared/components/ui/      -- shadcn-vendored components (we don't author the internals)
#   - src/shared/components/map/route-colors.ts  -- MapLibre bridge (HSL strings)
#   - src/shared/components/map/style.ts         -- MapLibre style spec
#   - src/shared/lib/branding.ts                 -- PWA manifest / browser-chrome hexes
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# grep -n output is "path:line:text". Match path-prefix; do not anchor with $
# or matches against the full grep line never fire.
ALLOWLIST_REGEX='^(src/app/globals\.css|tailwind\.config\.ts|src/shared/components/ui/|src/shared/components/map/(route-colors|style)\.ts|src/shared/lib/branding\.ts)'

EXIT=0

# Hex literals in TSX/TS source. Filter out HTML entities like `&#039;`.
HEX_HITS=$(grep -REn --include='*.ts' --include='*.tsx' \
  -e '#[0-9a-fA-F]{3,8}\b' \
  src 2>/dev/null \
  | grep -Ev '&#[0-9a-fA-F]+;' \
  | grep -Ev "$ALLOWLIST_REGEX" || true)
if [ -n "$HEX_HITS" ]; then
  echo "lint:design — raw hex colors found in feature code:"
  echo "$HEX_HITS"
  EXIT=1
fi

# Arbitrary Tailwind values like bg-[#...], p-[13px], gap-[7px], text-[15px].
ARB_HITS=$(grep -REn --include='*.ts' --include='*.tsx' \
  -e '\b(bg|text|border|p[xytrbl]?|m[xytrbl]?|gap|w|h)-\[' \
  src 2>/dev/null \
  | grep -Ev "$ALLOWLIST_REGEX" || true)
if [ -n "$ARB_HITS" ]; then
  echo "lint:design — arbitrary Tailwind values found in feature code:"
  echo "$ARB_HITS"
  EXIT=1
fi

if [ "$EXIT" -ne 0 ]; then
  echo
  echo "Reach for a token (see src/app/globals.css) or extend the design system."
  echo "See docs/development/conventions.md \"Design system\"."
fi
exit "$EXIT"
