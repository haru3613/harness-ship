#!/usr/bin/env bash
set -euo pipefail

base_ref="${1:-HEAD^}"
current_ref="${2:-HEAD}"
repo_root="$(git rev-parse --show-toplevel)"
lifecycle_tmp_dir="$(mktemp -d)"

cleanup_lifecycle_tmp() {
  rm -rf "${lifecycle_tmp_dir}"
}
trap cleanup_lifecycle_tmp EXIT

fresh_dir="${lifecycle_tmp_dir}/fresh"
upgrade_dir="${lifecycle_tmp_dir}/upgrade"
mkdir -p "${fresh_dir}" "${upgrade_dir}"

archive_ref() {
  local ref="$1"
  local destination="$2"
  git -C "${repo_root}" archive "${ref}" | tar -x -C "${destination}"
}

manifest_version() {
  jq -r '.version' "$1/.codex-plugin/plugin.json"
}

validate_generic_install() {
  local install_root="$1"

  jq empty \
    "${install_root}/.codex-plugin/plugin.json" \
    "${install_root}/.claude-plugin/plugin.json" \
    "${install_root}/.claude-plugin/marketplace.json" \
    "${install_root}/.agents/plugins/marketplace.json"

  local codex_version
  local claude_version
  codex_version="$(jq -r '.version' "${install_root}/.codex-plugin/plugin.json")"
  claude_version="$(jq -r '.version' "${install_root}/.claude-plugin/plugin.json")"
  test "${codex_version}" = "${claude_version}"
  test "$(jq -r '.skills' "${install_root}/.codex-plugin/plugin.json")" = "./skills/"

  python3 - "${install_root}" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
skills = sorted((root / "skills").glob("*/SKILL.md"))
if not skills:
    raise SystemExit("no skills discovered after install")
for skill in skills:
    match = re.search(r"(?m)^name:\s*(\S+)\s*$", skill.read_text(encoding="utf-8"))
    if match is None or match.group(1) != skill.parent.name:
        raise SystemExit(f"invalid discovered skill: {skill}")
print(len(skills))
PY
}

validate_current_install() {
  local install_root="$1"
  validate_generic_install "${install_root}" >/dev/null

  local required
  for required in \
    "skills/bug-workflow/SKILL.md" \
    "skills/diagnose/diagnosis-receipt-template.md" \
    "skills/implement/defect-repair-receipt-template.md" \
    "skills/testing-workflow/qa-handoff-template.md"; do
    test -f "${install_root}/${required}"
  done
}

archive_ref "${current_ref}" "${fresh_dir}"
validate_current_install "${fresh_dir}"

archive_ref "${base_ref}" "${upgrade_dir}"
validate_generic_install "${upgrade_dir}" >/dev/null
base_version="$(manifest_version "${upgrade_dir}")"

rm -rf "${upgrade_dir}"
mkdir -p "${upgrade_dir}"
archive_ref "${current_ref}" "${upgrade_dir}"
validate_current_install "${upgrade_dir}"
current_version="$(manifest_version "${upgrade_dir}")"

python3 - "${base_version}" "${current_version}" <<'PY'
import sys

base = tuple(int(part) for part in sys.argv[1].split("."))
current = tuple(int(part) for part in sys.argv[2].split("."))
if current < base:
    raise SystemExit(f"version regressed: {base} -> {current}")
PY

current_sha="$(git -C "${repo_root}" rev-parse "${current_ref}")"
base_sha="$(git -C "${repo_root}" rev-parse "${base_ref}")"
skill_count="$(find "${fresh_dir}/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')"

echo "fresh-install receipt: source=${current_sha} version=${current_version} discovered-skills=${skill_count}"
echo "upgrade receipt: from=${base_sha}:${base_version} to=${current_sha}:${current_version} discovered-skills=${skill_count}"
