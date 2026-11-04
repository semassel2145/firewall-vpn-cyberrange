#!/usr/bin/env bash
set -euo pipefail

URL="https://seedsecuritylabs.org/Labs_16.04/Networking/VPN/files/vpn.zip"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v unzip >/dev/null || { echo "unzip is required" >&2; exit 1; }

echo "Downloading the official SEED sample archive..."
curl --fail --location --proto '=https' --tlsv1.2 "$URL" -o "$TMP/vpn.zip"
unzip -q "$TMP/vpn.zip" -d "$TMP/extracted"

for filename in vpnclient.c vpnserver.c; do
  mapfile -t matches < <(find "$TMP/extracted" -type f -name "$filename")
  if [[ ${#matches[@]} -ne 1 ]]; then
    echo "Expected exactly one $filename in the SEED archive; found ${#matches[@]}" >&2
    echo "Archive contents:" >&2
    find "$TMP/extracted" -maxdepth 4 -type f -print >&2
    exit 2
  fi
  install -m 0644 "${matches[0]}" "$ROOT/seed-source/$filename"
done

echo "Updated seed-source/vpnclient.c and seed-source/vpnserver.c from the official SEED archive."
echo "Re-run scripts/validate.py, then commit the updated source files."
