#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./install.sh <workspace-dir> [--dry-run]     install into a workspace (VS Code + Copilot CLI)
  ./install.sh --personal [--dry-run]          install skills and agents into ~/.copilot (all workspaces, Copilot CLI + VS Code)
  ./install.sh <workspace-dir> --uninstall     remove starter-owned files (keeps generated state and house-style files)

Re-running is safe: starter-owned files are updated, generated files
(house-style-*.instructions.md, .github/mule-starter/profile.md, rulesets, lessons, log) are never overwritten,
and existing AGENTS.md / copilot-instructions.md keep their own content (only the mule-starter block is replaced).
EOF
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/template"
DRY=0
MODE=workspace
TARGET=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --personal) MODE=personal ;;
    --uninstall) MODE=uninstall ;;
    -h|--help) usage; exit 0 ;;
    *) TARGET="$arg" ;;
  esac
done

run() { if [ "$DRY" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }
note() { echo "• $*"; }

command -v python3 >/dev/null || { echo "python3 is required (scripts and block merge)"; exit 1; }

SKILLS=$(cd "$SRC/.github/skills" && ls -d */ | tr -d /)
AGENTS=$(cd "$SRC/.github/agents" && ls *.agent.md)
SHIPPED_INSTRUCTIONS=$(cd "$SRC/.github/instructions" && ls *.instructions.md)
PROMPTS=$(cd "$SRC/.github/prompts" && ls *.prompt.md)

merge_block() {
  local src="$1" dst="$2"
  if [ "$DRY" = 1 ]; then echo "[dry-run] merge mule-starter block $src -> $dst"; return; fi
  mkdir -p "$(dirname "$dst")"
  python3 - "$src" "$dst" <<'PY'
import re, sys, pathlib
src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
block = re.search(r"<!-- mule-starter:begin.*?<!-- mule-starter:end -->", src.read_text(), re.S).group(0)
if not dst.exists():
    dst.write_text(block + "\n")
    print(f"  created {dst}")
    sys.exit()
text = dst.read_text()
if "<!-- mule-starter:begin" in text:
    new = re.sub(r"<!-- mule-starter:begin.*?<!-- mule-starter:end -->", lambda m: block, text, flags=re.S)
    print(f"  updated starter block in {dst}")
else:
    new = block + "\n\n" + text
    print(f"  prepended starter block to existing {dst} (your content kept below it)")
dst.write_text(new)
PY
}

copy_dir() {
  local from="$1" to="$2"
  run mkdir -p "$to"
  if [ "$DRY" = 1 ]; then echo "[dry-run] sync $from -> $to"; return; fi
  rm -rf "$to"
  mkdir -p "$(dirname "$to")"
  cp -R "$from" "$to"
  find "$to" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
  find "$to" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
}

if [ "$MODE" = personal ]; then
  DEST="$HOME/.copilot"
  note "Installing personal skills into $DEST/skills and agents into $DEST/agents"
  for s in $SKILLS; do copy_dir "$SRC/.github/skills/$s" "$DEST/skills/$s"; done
  run mkdir -p "$DEST/agents"
  for a in $AGENTS; do run cp "$SRC/.github/agents/$a" "$DEST/agents/$a"; done
  note "Done. Per-workspace parts (AGENTS.md, instructions, /mule-init output) still need: ./install.sh <workspace-dir>"
  exit 0
fi

[ -n "$TARGET" ] || { usage; exit 1; }
[ -d "$TARGET" ] || { echo "Not a directory: $TARGET"; exit 1; }
WS="$(cd "$TARGET" && pwd)"
GH="$WS/.github"

if [ "$MODE" = uninstall ]; then
  note "Removing starter-owned files from $WS"
  for s in $SKILLS; do run rm -rf "$GH/skills/$s"; done
  for a in $AGENTS; do run rm -f "$GH/agents/$a"; done
  for i in $SHIPPED_INSTRUCTIONS; do run rm -f "$GH/instructions/$i"; done
  for p in $PROMPTS; do run rm -f "$GH/prompts/$p"; done
  for f in "$WS/AGENTS.md" "$GH/copilot-instructions.md"; do
    [ -f "$f" ] || continue
    if [ "$DRY" = 1 ]; then echo "[dry-run] strip starter block from $f"; continue; fi
    python3 - "$f" <<'PY'
import re, sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = re.sub(r"<!-- mule-starter:begin.*?<!-- mule-starter:end -->\n*", "", t, flags=re.S)
p.write_text(t) if t.strip() else p.unlink()
PY
  done
  note "Kept: house-style-*.instructions.md and .github/mule-starter/ (delete by hand if you want them gone)"
  exit 0
fi

note "Installing into $WS"
merge_block "$SRC/AGENTS.md" "$WS/AGENTS.md"
merge_block "$SRC/.github/copilot-instructions.md" "$GH/copilot-instructions.md"

run mkdir -p "$GH/instructions" "$GH/agents" "$GH/prompts" "$GH/skills"
for i in $SHIPPED_INSTRUCTIONS; do run cp "$SRC/.github/instructions/$i" "$GH/instructions/$i"; done
for a in $AGENTS; do run cp "$SRC/.github/agents/$a" "$GH/agents/$a"; done
for p in $PROMPTS; do run cp "$SRC/.github/prompts/$p" "$GH/prompts/$p"; done
for s in $SKILLS; do copy_dir "$SRC/.github/skills/$s" "$GH/skills/$s"; done

STATE="$GH/mule-starter"
run mkdir -p "$STATE/rulesets" "$STATE/memory"
[ -f "$STATE/README.md" ] || run cp "$SRC/.github/mule-starter/README.md" "$STATE/README.md"
[ -f "$STATE/memory/lessons.md" ] || run cp "$SRC/.github/mule-starter/memory/lessons.md" "$STATE/memory/lessons.md"
[ -f "$STATE/log.md" ] || { if [ "$DRY" = 1 ]; then echo "[dry-run] create $STATE/log.md"; else printf '# Change log (one line per change, newest last)\n' > "$STATE/log.md"; fi; }
if [ ! -f "$STATE/installed-at" ]; then
  if [ "$DRY" = 1 ]; then echo "[dry-run] write $STATE/installed-at"; else date +%F > "$STATE/installed-at"; fi
fi

note "Installed: $(echo $SKILLS | wc -w | tr -d ' ') skills, $(echo $AGENTS | wc -w | tr -d ' ') agents, $(echo $SHIPPED_INSTRUCTIONS | wc -w | tr -d ' ') instruction files, $(echo $PROMPTS | wc -w | tr -d ' ') prompts"
[ -d "$WS/.claude" ] && note "Found .claude/ here: Copilot also reads .claude/skills and CLAUDE.md — see README › 'Workspace that already has Claude Code setup'."
note "Next: open the workspace in VS Code, Agent mode, run /mule-init"
