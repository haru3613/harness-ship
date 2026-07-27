#!/usr/bin/env bash
set -euo pipefail

base_ref="${1:-HEAD^}"
current_ref="${2:-HEAD}"
lifecycle_mode="${3:-pr}"
repo_root="$(git rev-parse --show-toplevel)"
lifecycle_tmp_dir="$(mktemp -d)"

case "${lifecycle_mode}" in
  pr|release)
    ;;
  *)
    echo "lifecycle mode must be pr or release" >&2
    exit 2
    ;;
esac

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

  python3 "${repo_root}/scripts/check_release_contract.py" \
    version-state check --repo "${install_root}" --ref WORKTREE >/dev/null

  local required
  for required in \
    "agents/harness-ship-independent-verifier.md" \
    "scripts/role_binding_contract.py" \
    "skills/bug-workflow/SKILL.md" \
    "skills/diagnose/diagnosis-receipt-template.md" \
    "skills/implement/defect-repair-receipt-template.md" \
    "skills/testing-workflow/qa-handoff-template.md"; do
    test -f "${install_root}/${required}"
  done

  local agent_path
  while IFS= read -r -d '' agent_path; do
    python3 "${install_root}/scripts/role_binding_contract.py" \
      validate-agent "${agent_path}" >/dev/null
  done < <(find "${install_root}/agents" -mindepth 1 -maxdepth 1 -name '*.md' -print0)

  python3 "${install_root}/scripts/role_binding_contract.py" self-test >/dev/null

  if command -v claude >/dev/null 2>&1; then
    (
      cd "${install_root}"
      claude plugin validate --strict .
    )
    local claude_inventory
    claude_inventory="$(
      cd "${install_root}"
      claude --plugin-dir . plugin details harness-ship
    )"
    grep -Eq \
      'Agents \(1\).*harness-ship-independent-verifier' \
      <<<"${claude_inventory}"
  fi
}

archive_ref "${current_ref}" "${fresh_dir}"
archive_ref "${base_ref}" "${upgrade_dir}"
base_version="$(manifest_version "${upgrade_dir}")"
current_version="$(manifest_version "${fresh_dir}")"

if test "${lifecycle_mode}" = "pr"; then
  python3 "${repo_root}/scripts/check_release_contract.py" \
    pr --repo "${repo_root}" "${base_ref}" "${current_ref}"
else
  python3 "${repo_root}/scripts/check_release_contract.py" \
    version-state check --repo "${repo_root}" --ref "${current_ref}"
  test "${base_version}" != "${current_version}"
fi

validate_current_install "${fresh_dir}"
validate_generic_install "${upgrade_dir}" >/dev/null

rm -rf "${upgrade_dir}"
mkdir -p "${upgrade_dir}"
archive_ref "${current_ref}" "${upgrade_dir}"
validate_current_install "${upgrade_dir}"

current_sha="$(git -C "${repo_root}" rev-parse "${current_ref}")"
base_sha="$(git -C "${repo_root}" rev-parse "${base_ref}")"
skill_count="$(find "${fresh_dir}/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')"
agent_count="$(find "${fresh_dir}/agents" -mindepth 1 -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"

echo "fresh-install receipt: source=${current_sha} version=${current_version} discovered-skills=${skill_count} discovered-agents=${agent_count}"
echo "upgrade receipt: from=${base_sha}:${base_version} to=${current_sha}:${current_version} discovered-skills=${skill_count} discovered-agents=${agent_count}"
