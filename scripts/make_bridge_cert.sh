#!/usr/bin/env bash
# Local TLS certificate for the engine bridge (scripts/bridge_server.py).
#
# Chrome silently drops an HTTPS page's request to http://127.0.0.1, so the
# bridge has to speak TLS. This makes a LEAF-ONLY certificate: CA:FALSE, valid
# for localhost alone, 14-day expiry. Even fully trusted it can vouch for
# nothing except this machine's loopback.
#
# The key is gitignored on purpose. Regenerate rather than share.
set -euo pipefail
cd "$(dirname "$0")/../data/draftrig/tls"
cat > san.cnf <<'CNF'
[req]
distinguished_name=dn
x509_extensions=v3
prompt=no
[dn]
CN=localhost
[v3]
subjectAltName=DNS:localhost,IP:127.0.0.1
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
CNF
openssl req -x509 -newkey rsa:2048 -sha256 -days 14 -nodes \
  -keyout key.pem -out cert.pem -config san.cnf 2>/dev/null
echo "wrote cert.pem / key.pem"
openssl x509 -in cert.pem -noout -ext basicConstraints -ext subjectAltName -enddate
