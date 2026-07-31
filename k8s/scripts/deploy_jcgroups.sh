#!/bin/sh
#
# 目的: make_jcgroups_manifests.sh が生成したディレクトリを k8s へ適用する
#
# 引数
# 1. generated_dir : <output_dir>/<VHOST> (manifests / conf / ssl / sp を含む)
# 2. --skip-db-init: DB 初期化 Job を実行しない (2回目以降のデプロイ)
#
# 例
#   ./deploy_jcgroups.sh /tmp/generated/groups.example.ac.jp
#   ./deploy_jcgroups.sh /tmp/generated/groups.example.ac.jp --skip-db-init
#
# ファイル由来の Secret (server.config.toml / 各証明書) はマニフェスト化すると
# 中身が Git に載るので、ここで kubectl create secret して作る。

set -e

if [ $# -lt 1 ] || [ ! -d "$1" ]; then
  echo "usage : $0 generated_dir [--skip-db-init]"
  exit 3
fi

GEN_DIR=$(cd "$1" && pwd)
SKIP_DB_INIT=${2:-}

MANIFEST_DIR="$GEN_DIR/manifests"
CONF_DIR="$GEN_DIR/conf"
SSL_DIR="$GEN_DIR/ssl"
SP_DIR="$GEN_DIR/sp"
INST_DIR="$GEN_DIR/institutions"

if [ ! -f "$GEN_DIR/params.env" ]; then
  echo "ERROR: $GEN_DIR/params.env がない。make_jcgroups_manifests.sh の出力先を指定すること" >&2
  exit 3
fi

# shellcheck disable=SC1091
. "$GEN_DIR/params.env"
: "${NAMESPACE:=jcgroups}"
DOMAIN_NAME=$(echo "$VHOST" | tr '._' '-')

KC="kubectl -n $NAMESPACE"

date
echo "=== deploy $VHOST (namespace=$NAMESPACE) ==="

# ------------------------------------------------------------
# Namespace
# ------------------------------------------------------------
kubectl apply -f "$MANIFEST_DIR/namespace.yaml"

# ------------------------------------------------------------
# ファイル由来の Secret / ConfigMap
#
# 何度でも流せるように create --dry-run=client | apply の形にする。
# ------------------------------------------------------------
apply_secret() {
  # $1 以降を kubectl create secret の引数として渡す
  $KC create secret "$@" --dry-run=client -o yaml | $KC apply -f -
}

echo "--- secrets"
apply_secret generic "$DOMAIN_NAME-secret" \
  --from-file=server.config.toml="$CONF_DIR/server.config.toml"

# nginx / Shibboleth SP のサーバ証明書 (Pod にマウントする)
apply_secret generic "$DOMAIN_NAME-tls" \
  --from-file=server.crt="$SSL_DIR/server.crt" \
  --from-file=server.key="$SSL_DIR/server.key"

# Ingress の TLS Secret (kubernetes.io/tls 形式が要る)
apply_secret tls "$DOMAIN_NAME-cert" \
  --cert="$SSL_DIR/server.crt" \
  --key="$SSL_DIR/server.key"

# mAP Core 接続用クライアント証明書 ([sp] crt / key)
apply_secret generic "$DOMAIN_NAME-sp-cert" \
  --from-file=server.crt="$SP_DIR/server.crt" \
  --from-file=server.key="$SP_DIR/server.key"

# 機関別クライアント証明書。キー名は <FQDN>.server.crt|key
# (make_jcgroups_manifests.sh が deploy-web.yaml の items[].path をこの規則で作る)
if [ -d "$INST_DIR" ]; then
  set --
  for d in "$INST_DIR"/*; do
    [ -d "$d" ] || continue
    fqdn=$(basename "$d")
    set -- "$@" \
      --from-file="$fqdn.server.crt=$d/server.crt" \
      --from-file="$fqdn.server.key=$d/server.key"
  done
  if [ $# -gt 0 ]; then
    apply_secret generic "$DOMAIN_NAME-institution-certs" "$@"
  fi
fi

echo "--- configmaps"
$KC create configmap "$DOMAIN_NAME-shibboleth2" \
  --from-file=shibboleth2.xml="$CONF_DIR/shibboleth2.xml" \
  --dry-run=client -o yaml | $KC apply -f -

# ------------------------------------------------------------
# マニフェスト (Deployment 以外)
# ------------------------------------------------------------
echo "--- manifests"
kubectl apply -f "$MANIFEST_DIR/configmap.yaml"
# 検証用ミドルウェアを立てるときだけ生成される (PostgreSQL のパスワード)
if [ -f "$MANIFEST_DIR/secret.yaml" ]; then
  kubectl apply -f "$MANIFEST_DIR/secret.yaml"
fi
# STORAGE_TYPE=emptydir では生成されない
if [ -f "$MANIFEST_DIR/volume-pv.yaml" ]; then
  kubectl apply -f "$MANIFEST_DIR/volume-pv.yaml"
fi
if [ -f "$MANIFEST_DIR/volume-pvc.yaml" ]; then
  kubectl apply -f "$MANIFEST_DIR/volume-pvc.yaml"
fi
kubectl apply -f "$MANIFEST_DIR/service.yaml"
kubectl apply -f "$MANIFEST_DIR/ingress.yaml"

if [ -f "$MANIFEST_DIR/middleware.yaml" ]; then
  echo "--- middleware (検証用)"
  kubectl apply -f "$MANIFEST_DIR/middleware.yaml"
  $KC wait --for=condition=available --timeout=300s \
    "deployment/$DOMAIN_NAME-postgres" \
    "deployment/$DOMAIN_NAME-redis" \
    "deployment/$DOMAIN_NAME-rabbitmq"
fi

# ------------------------------------------------------------
# DB 初期化 Job
#
# Job の spec は immutable なので、作り直す前に消す。
# ------------------------------------------------------------
if [ "$SKIP_DB_INIT" = "--skip-db-init" ]; then
  echo "--- db-init: スキップ"
else
  echo "--- db-init"
  $KC delete job "$DOMAIN_NAME-db-init" --ignore-not-found
  kubectl apply -f "$MANIFEST_DIR/job-db-init.yaml"
  if ! $KC wait --for=condition=complete --timeout=300s "job/$DOMAIN_NAME-db-init"; then
    echo "ERROR: db-init Job が完了しなかった。ログ:" >&2
    $KC logs "job/$DOMAIN_NAME-db-init" --tail=50 >&2 || true
    exit 7
  fi
fi

# ------------------------------------------------------------
# 本体 (nginx + web + worker)
# ------------------------------------------------------------
echo "--- deploy-web"
kubectl apply -f "$MANIFEST_DIR/deploy-web.yaml"
$KC rollout status "deployment/$DOMAIN_NAME-web" --timeout=600s

echo ""
$KC get pod -l "app=$DOMAIN_NAME-nginx" -o wide
$KC get svc "$DOMAIN_NAME-nginx"
date
