#!/usr/bin/env bash
# Prepare one sample batch locally. This script never sends or publishes anything.
set -euo pipefail
if [ "$(id -un)" != 'ignidi-hermes' ]; then
  echo 'Jalankan sebagai user ignidi-hermes, bukan root atau user Rama.' >&2
  exit 1
fi
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$(cd -- "$studio_dir/../.." && pwd)"
cd "$studio_dir"
export IGNIDI_LOGO_PATH="$source_dir/public/ignidi-labs.jpeg"
content_state="${IGNIDI_CONTENT_STATE:-$HOME/.local/state/ignidi-content}"
mkdir -p "$content_state"
chmod 700 "$content_state"
node render.mjs samples/lead.json "$content_state/preview.jpg"
python3 content_queue.py --state "$content_state" add samples/lead.json --image "$content_state/preview.jpg"
python3 send_review.py --state "$content_state" --pending --limit 2
printf '\nDry run selesai. Belum ada pesan atau posting dikirim. Untuk kirim review:\n'
printf 'python3 send_review.py --pending --limit 2 --send\n'
