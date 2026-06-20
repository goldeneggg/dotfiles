#!/bin/bash
set -euo pipefail

VERSION="${1:?Usage: $0 <version> <gpg_key>}"
GPG_KEY="${2:?Usage: $0 <version> <gpg_key>}"

echo "Installing 1Password CLI v${VERSION}..."
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "${TEMP_DIR}"' EXIT
curl -sSfL "https://cache.agilebits.com/dist/1P/op2/pkg/v${VERSION}/op_darwin_arm64_v${VERSION}.zip" -o "${TEMP_DIR}/op.zip"
unzip -q "${TEMP_DIR}/op.zip" -d "${TEMP_DIR}"
gpg --keyserver hkps://keyserver.ubuntu.com --receive-keys "${GPG_KEY}"
gpg --verify "${TEMP_DIR}/op.sig" "${TEMP_DIR}/op"
mkdir -p "${HOME}/bin"
mv "${TEMP_DIR}/op" "${HOME}/bin/op"
test -x "${HOME}/bin/op" || chmod 755 "${HOME}/bin/op"
echo "1Password CLI v${VERSION} installed successfully at ${HOME}/bin/op"
