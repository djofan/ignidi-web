#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -un)" != 'ignidi-hermes' ]; then
  echo 'Jalankan sebagai ignidi-hermes melalui sudo -iu ignidi-hermes, bukan root/Rama.' >&2
  exit 1
fi
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hermes_dir="${HERMES_HOME:-$HOME/.hermes}"
plugin_dir="$hermes_dir/plugins/ignidi-review"
python3 -m unittest discover -s "$studio_dir" -p 'test_*.py'
python3 - "$studio_dir" "$hermes_dir" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from send_review import load_config
load_config(Path(sys.argv[2])/'.env')
print('Konfigurasi DM pemilik valid; token tidak ditampilkan.')
PY
if [ -e "$plugin_dir" ] && [ ! -f "$plugin_dir/.ignidi-managed" ]; then
  echo 'Folder plugin sudah ada dan bukan milik pemasang ini. Periksa dulu sebelum menimpa.' >&2
  exit 1
fi
mkdir -p "$plugin_dir"
chmod 700 "$plugin_dir"
cp "$studio_dir/hermes_plugin/plugin.yaml" "$plugin_dir/"
cp "$studio_dir/hermes_plugin/entrypoint.py" "$plugin_dir/__init__.py"
cp "$studio_dir/content_queue.py" "$studio_dir/send_review.py" "$studio_dir/review_workflow.py" "$studio_dir/buffer_drafts.py" "$studio_dir/buffer_media.py" "$plugin_dir/"
printf '%s\n' "$studio_dir" > "$plugin_dir/studio-path.txt"
touch "$plugin_dir/.ignidi-managed"
hermes plugins enable ignidi-review
hermes config set plugins.entries.ignidi-review.allow_gateway_injection true
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
systemctl --user restart hermes-gateway.service
systemctl --user is-active hermes-gateway.service
echo 'Plugin dipasang dan gateway dimulai ulang. Uji /statuskonten lewat DM Telegram.'
echo 'Tidak ada token Meta, kunci reviewer, publisher, cron, atau service user lain yang diubah.'
