#!/bin/sh
#
# 目的: deploy_jcgroups.sh で作ったリソースを消す
#
# 引数
# 1. generated_dir : make_jcgroups_manifests.sh の出力ディレクトリ
# 2. --all         : Namespace / PV / PVC も消す (データが消えるので既定では残す)
#
# 例
#   ./delete_jcgroups.sh /tmp/generated/groups.example.ac.jp
#   ./delete_jcgroups.sh /tmp/generated/groups.example.ac.jp --all

set -e

if [ $# -lt 1 ] || [ ! -d "$1" ]; then
  echo "usage : $0 generated_dir [--all]"
  exit 3
fi

GEN_DIR=$(cd "$1" && pwd)
MODE=${2:-}
MANIFEST_DIR="$GEN_DIR/manifests"

# shellcheck disable=SC1091
. "$GEN_DIR/params.env"
: "${NAMESPACE:=jcgroups}"
DOMAIN_NAME=$(echo "$VHOST" | tr '._' '-')
KC="kubectl -n $NAMESPACE"

echo "=== delete $VHOST (namespace=$NAMESPACE) ==="

$KC delete -f "$MANIFEST_DIR/deploy-web.yaml" --ignore-not-found
$KC delete job "$DOMAIN_NAME-db-init" --ignore-not-found
$KC delete -f "$MANIFEST_DIR/ingress.yaml" --ignore-not-found
$KC delete -f "$MANIFEST_DIR/service.yaml" --ignore-not-found

if [ -f "$MANIFEST_DIR/middleware.yaml" ]; then
  $KC delete -f "$MANIFEST_DIR/middleware.yaml" --ignore-not-found
fi

$KC delete secret \
  "$DOMAIN_NAME-secret" \
  "$DOMAIN_NAME-tls" \
  "$DOMAIN_NAME-cert" \
  "$DOMAIN_NAME-sp-cert" \
  "$DOMAIN_NAME-institution-certs" \
  "$DOMAIN_NAME-middleware" --ignore-not-found
$KC delete configmap "$DOMAIN_NAME-configmap" "$DOMAIN_NAME-shibboleth2" --ignore-not-found

if [ "$MODE" = "--all" ]; then
  echo "--- PVC / PV / Namespace も削除する (データが消える)"
  if [ -f "$MANIFEST_DIR/volume-pvc.yaml" ]; then
    $KC delete -f "$MANIFEST_DIR/volume-pvc.yaml" --ignore-not-found
  fi
  $KC delete pvc "$DOMAIN_NAME-pgdata-pvc" --ignore-not-found
  if [ -f "$MANIFEST_DIR/volume-pv.yaml" ]; then
    kubectl delete -f "$MANIFEST_DIR/volume-pv.yaml" --ignore-not-found
  fi
  kubectl delete namespace "$NAMESPACE" --ignore-not-found
fi

echo "done"
