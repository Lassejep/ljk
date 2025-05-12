#!/bin/bash

which openssl >/dev/null || { echo "openssl not found"; exit 1; }

if [ -z "$1" ]; then
    echo "Usage: $0 <certs_dir>"
    exit 1
fi
CERTS_DIR="$1"
if [ ! -d "$CERTS_DIR" ]; then
    mkdir -p $CERTS_DIR
fi
SERVER_KEY="${CERTS_DIR}/server.key"
SERVER_CSR="${CERTS_DIR}/server.csr"
SERVER_CERT="${CERTS_DIR}/server.crt"
CLIENT_KEY="${CERTS_DIR}/client.key"
CLIENT_CSR="${CERTS_DIR}/client.csr"
CLIENT_CERT="${CERTS_DIR}/client.crt"

if ! openssl x509 -checkend 0 -noout -in ${SERVER_CERT} >/dev/null; then
    openssl genpkey -algorithm RSA -out ${SERVER_KEY}
    openssl req -new -key ${SERVER_KEY} -out ${SERVER_CSR} -subj "/CN=example-server"
    openssl x509 -req -in ${SERVER_CSR} -signkey ${SERVER_KEY} -out ${SERVER_CERT} -days 365 -sha256
fi
if ! openssl x509 -checkend 0 -noout -in ${CLIENT_CERT} >/dev/null; then
    openssl genpkey -algorithm RSA -out ${CLIENT_KEY}
    openssl req -new -key ${CLIENT_KEY} -out ${CLIENT_CSR} -subj "/CN=example-client"
    openssl x509 -req -in ${CLIENT_CSR} -signkey ${CLIENT_KEY} -out ${CLIENT_CERT} -days 365 -sha256
fi
