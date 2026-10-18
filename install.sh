#!/usr/bin/env bash
# 把 cn-jobs-search 安装到目标 ai-job-search 仓库。
# 用法: ./install.sh /path/to/ai-job-search [--force]
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/.agents/skills/cn-jobs-search"
DEST_ROOT="${1:-}"
FORCE="${2:-}"

if [[ -z "$DEST_ROOT" ]]; then
  echo "用法: $0 /path/to/ai-job-search [--force]" >&2
  exit 2
fi
if [[ ! -d "$DEST_ROOT" ]]; then
  echo "目标目录不存在: $DEST_ROOT" >&2
  exit 2
fi

DEST="$DEST_ROOT/.agents/skills/cn-jobs-search"
if [[ -e "$DEST" && "$FORCE" != "--force" ]]; then
  echo "已存在: $DEST"
  echo "加 --force 覆盖，或先手动备份。" >&2
  exit 1
fi

mkdir -p "$DEST_ROOT/.agents/skills"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"

echo "已安装到: $DEST"
echo
echo "验证："
echo "  cd $DEST_ROOT"
echo "  python3 .agents/skills/cn-jobs-search/cli/src/cli.py search -q llm -p demo"
echo
echo "测试："
echo "  cd .agents/skills/cn-jobs-search/cli && python3 -m unittest discover -s tests -p 'test_*.py'"
