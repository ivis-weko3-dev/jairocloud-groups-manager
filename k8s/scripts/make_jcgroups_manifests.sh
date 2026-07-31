#!/bin/sh
#
# 目的: params.env を読み、manifest_template/*.yaml の __PLACEHOLDER__ を
#       置換した実マニフェストと、環境用の設定ファイル / 証明書を生成する
#
# 引数
# 1. params_file : パラメータファイル (deploy/jcgroups/params.env.example を参照)
# 2. output_dir  : 生成先ディレクトリ
#
# 例
#   ./make_jcgroups_manifests.sh ../deploy/jcgroups/params.env /tmp/generated
#
# 生成物
#   <output_dir>/<VHOST>/manifests/*.yaml   … kubectl apply するマニフェスト
#   <output_dir>/<VHOST>/conf/server.config.toml
#   <output_dir>/<VHOST>/conf/shibboleth2.xml
#   <output_dir>/<VHOST>/ssl/server.crt|key … nginx / SP のサーバ証明書
#   <output_dir>/<VHOST>/sp/server.crt|key  … mAP Core 接続用クライアント証明書
#   <output_dir>/<VHOST>/institutions/...   … 機関別クライアント証明書
#   <output_dir>/<VHOST>/params.env         … 使ったパラメータの控え
#
# 【注意】生成物には secret_key・DB パスワード・秘密鍵が入る。Git に入れないこと。

set -e

if [ $# != 2 ]; then
  echo "usage : $0 params_file output_dir"
  exit 3
fi

if [ ! -f "$1" ]; then
  echo "usage : $0 params_file output_dir"
  echo "  params_file が見つからない: $1"
  exit 3
fi

PARAMS_FILE=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
OUTPUT_DIR=$2

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
TEMPLATE_DIR="$REPO_ROOT/k8s/deploy/jcgroups/manifest_template"
MIDDLEWARE_TEMPLATE_DIR="$REPO_ROOT/k8s/deploy/middleware/manifest_template"

# ------------------------------------------------------------
# パラメータ読み込みと既定値
# ------------------------------------------------------------
# shellcheck disable=SC1090
. "$PARAMS_FILE"

: "${NAMESPACE:=jcgroups}"
: "${IMAGE_PULL_POLICY:=Always}"
: "${REPLICAS:=2}"
: "${MEMORY_REQUEST:=512Mi}"
: "${MEMORY_LIMIT:=1Gi}"
: "${WORKER_MEMORY_LIMIT:=2Gi}"
: "${NGINX_MEMORY_LIMIT:=512Mi}"
: "${CELERY_CONCURRENCY:=4}"
: "${CONFIG_REVISION:=1}"
: "${SERVICE_TYPE:=NodePort}"
: "${INGRESS_CLASS:=nginx}"
: "${MAX_UPLOAD_SIZE:=10m}"
: "${STORAGE_TYPE:=nfs}"
: "${STORAGE_SIZE:=20Gi}"
: "${STORAGE_CLASS:=nfs}"
: "${POSTGRES_HOST:=postgres}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:=jcgroups}"
: "${POSTGRES_USER:=jcgroups}"
: "${REDIS_CACHE_TYPE:=RedisSentinelCache}"
: "${REDIS_URL:=redis://redis:6379}"
: "${REDIS_SENTINEL_NODES:=}"
: "${REDIS_SENTINEL_MASTER:=mymaster}"
: "${REDIS_DB_APP_CACHE:=}"
: "${REDIS_DB_ACCOUNT_STORE:=}"
: "${REDIS_DB_RESULT_BACKEND:=}"
: "${REDIS_DB_GROUP_CACHE:=4}"
: "${RABBITMQ_URL:=amqp://guest:guest@rabbitmq:5672//}"
: "${MAP_CORE_BASE_URL:=https://sptest.cg.gakunin.jp}"
: "${DEPLOY_MIDDLEWARE:=false}"
: "${PGDATA_SIZE:=10Gi}"
: "${NODE_TYPE:=}"
: "${IMAGE_PULL_SECRET_NAME:=}"
: "${INSTITUTION_CERTS_DIR:=}"

for v in VHOST APP_IMAGE NGINX_IMAGE POSTGRES_PASSWORD; do
  eval "value=\$$v"
  if [ -z "$value" ]; then
    echo "ERROR: params.env の $v が空" >&2
    exit 4
  fi
done

if [ "$STORAGE_TYPE" != "nfs" ] && [ "$STORAGE_TYPE" != "emptydir" ]; then
  echo "ERROR: STORAGE_TYPE は nfs か emptydir" >&2
  exit 4
fi

if [ "$STORAGE_TYPE" = "emptydir" ] && [ "$REPLICAS" != "1" ]; then
  echo "ERROR: STORAGE_TYPE=emptydir では Pod 間でファイルを共有できないため" >&2
  echo "       REPLICAS=1 にすること (現在 $REPLICAS)" >&2
  exit 4
fi

if [ "$STORAGE_TYPE" = "nfs" ]; then
  for v in NFS_SERVER NFS_PATH; do
    eval "value=\$$v"
    if [ -z "$value" ]; then
      echo "ERROR: STORAGE_TYPE=nfs では $v が必須" >&2
      exit 4
    fi
  done
fi

if [ "$REDIS_CACHE_TYPE" != "RedisCache" ] && [ "$REDIS_CACHE_TYPE" != "RedisSentinelCache" ]; then
  echo "ERROR: REDIS_CACHE_TYPE は RedisCache か RedisSentinelCache" >&2
  exit 4
fi

if [ "$REDIS_CACHE_TYPE" = "RedisSentinelCache" ]; then
  if [ -z "$REDIS_SENTINEL_NODES" ]; then
    echo "ERROR: REDIS_CACHE_TYPE=RedisSentinelCache では" >&2
    echo "       REDIS_SENTINEL_NODES (host:port の空白区切り) が必須" >&2
    exit 4
  fi
  # 共有 Redis では DB 番号が機関ごとに払い出し済みなので、
  # リポジトリ既定値 (0/1/2) を暗黙に使わせない。
  for v in REDIS_DB_APP_CACHE REDIS_DB_ACCOUNT_STORE REDIS_DB_RESULT_BACKEND; do
    eval "value=\$$v"
    if [ -z "$value" ]; then
      echo "ERROR: 共有 Redis を使うので $v を明示すること" >&2
      echo "       (空き番号を運用側で確保してから指定する。README 参照)" >&2
      exit 4
    fi
  done
fi

# DB 番号の妥当性 (数値・重複なし)
REDIS_DBS=""
for v in REDIS_DB_APP_CACHE REDIS_DB_ACCOUNT_STORE REDIS_DB_RESULT_BACKEND REDIS_DB_GROUP_CACHE; do
  eval "value=\$$v"
  [ -z "$value" ] && continue
  case "$value" in
    ''|*[!0-9]*)
      echo "ERROR: $v は 0 以上の整数で指定すること (現在 '$value')" >&2
      exit 4 ;;
  esac
  for used in $REDIS_DBS; do
    if [ "$used" = "$value" ]; then
      echo "ERROR: Redis DB 番号 $value が重複している ($v)" >&2
      exit 4
    fi
  done
  REDIS_DBS="$REDIS_DBS $value"
done

if [ -z "${SECRET_KEY:-}" ]; then
  SECRET_KEY=$(openssl rand -hex 32)
  echo "SECRET_KEY を生成した (params.env に控えを残すこと)"
fi

# リソース名の接頭辞。FQDN の . と _ を - に置換する (weko-k8s と同じ流儀)。
DOMAIN_NAME=$(echo "$VHOST" | tr '._' '-')

OUT="$OUTPUT_DIR/$VHOST"
MANIFEST_DIR="$OUT/manifests"
CONF_DIR="$OUT/conf"
SSL_DIR="$OUT/ssl"
SP_DIR="$OUT/sp"
INST_DIR="$OUT/institutions"

rm -rf "$OUT"
mkdir -p "$MANIFEST_DIR" "$CONF_DIR" "$SSL_DIR" "$SP_DIR"

echo "create $VHOST (namespace=$NAMESPACE, prefix=$DOMAIN_NAME)"

# ------------------------------------------------------------
# 機関別証明書の items: ブロックを組み立てる
#
# Secret のキー名に "/" は使えないので、機関ごとの
# /var/mnt/<FQDN>/server.crt|key は items[].path で作る。
# キー名は <FQDN>.server.crt の形にする (deploy_jcgroups.sh も同じ規則で作る)。
# ------------------------------------------------------------
ITEMS_FILE=$(mktemp)
trap 'rm -f "$ITEMS_FILE"' EXIT

if [ -n "$INSTITUTION_CERTS_DIR" ]; then
  if [ ! -d "$INSTITUTION_CERTS_DIR" ]; then
    echo "ERROR: INSTITUTION_CERTS_DIR が存在しない: $INSTITUTION_CERTS_DIR" >&2
    exit 4
  fi
  mkdir -p "$INST_DIR"
  echo "            items:" >> "$ITEMS_FILE"
  found=0
  for d in "$INSTITUTION_CERTS_DIR"/*; do
    [ -d "$d" ] || continue
    fqdn=$(basename "$d")
    if [ ! -f "$d/server.crt" ] || [ ! -f "$d/server.key" ]; then
      echo "WARN: $fqdn に server.crt / server.key が揃っていないので飛ばす" >&2
      continue
    fi
    mkdir -p "$INST_DIR/$fqdn"
    cp "$d/server.crt" "$d/server.key" "$INST_DIR/$fqdn/"
    printf '              - key: %s.server.crt\n                path: %s/server.crt\n' \
      "$fqdn" "$fqdn" >> "$ITEMS_FILE"
    printf '              - key: %s.server.key\n                path: %s/server.key\n' \
      "$fqdn" "$fqdn" >> "$ITEMS_FILE"
    found=$((found + 1))
  done
  echo "  機関別証明書: $found 件"
  if [ "$found" -eq 0 ]; then
    : > "$ITEMS_FILE"
  fi
fi

# ------------------------------------------------------------
# マニフェスト生成
# ------------------------------------------------------------
render() {
  # $1: テンプレートファイル, $2: 出力先
  sed -e "s|__NAMESPACE__|$NAMESPACE|g" \
      -e "s|__DOMAIN_NAME__|$DOMAIN_NAME|g" \
      -e "s|__VHOST__|$VHOST|g" \
      -e "s|__APP_IMAGE__|$APP_IMAGE|g" \
      -e "s|__NGINX_IMAGE__|$NGINX_IMAGE|g" \
      -e "s|__IMAGE_PULL_POLICY__|$IMAGE_PULL_POLICY|g" \
      -e "s|__IMAGE_PULL_SECRET_NAME__|$IMAGE_PULL_SECRET_NAME|g" \
      -e "s|__NODE_TYPE__|$NODE_TYPE|g" \
      -e "s|__REPLICAS__|$REPLICAS|g" \
      -e "s|__MEMORY_REQUEST__|$MEMORY_REQUEST|g" \
      -e "s|__MEMORY_LIMIT__|$MEMORY_LIMIT|g" \
      -e "s|__WORKER_MEMORY_LIMIT__|$WORKER_MEMORY_LIMIT|g" \
      -e "s|__NGINX_MEMORY_LIMIT__|$NGINX_MEMORY_LIMIT|g" \
      -e "s|__CELERY_CONCURRENCY__|$CELERY_CONCURRENCY|g" \
      -e "s|__CONFIG_REVISION__|$CONFIG_REVISION|g" \
      -e "s|__SERVICE_TYPE__|$SERVICE_TYPE|g" \
      -e "s|__INGRESS_CLASS__|$INGRESS_CLASS|g" \
      -e "s|__MAX_UPLOAD_SIZE__|$MAX_UPLOAD_SIZE|g" \
      -e "s|__STORAGE_SIZE__|$STORAGE_SIZE|g" \
      -e "s|__STORAGE_CLASS__|$STORAGE_CLASS|g" \
      -e "s|__NFS_SERVER__|$NFS_SERVER|g" \
      -e "s|__NFS_PATH__|$NFS_PATH|g" \
      -e "s|__POSTGRES_DB__|$POSTGRES_DB|g" \
      -e "s|__POSTGRES_USER__|$POSTGRES_USER|g" \
      -e "s|__POSTGRES_PASSWORD__|$POSTGRES_PASSWORD|g" \
      -e "s|__PGDATA_SIZE__|$PGDATA_SIZE|g" \
      "$1" > "$2"

  # ---- マーカー行の処理 ----
  # `#__NAME__` 付きの行は「条件付きで出力する行」。
  # 有効化するときはマーカーだけを削り、無効化するときは行ごと消す。
  if [ -n "$IMAGE_PULL_SECRET_NAME" ]; then
    sed -i -e "s|#__IMAGE_PULL_SECRET__||" "$2"
  else
    sed -i -e "/#__IMAGE_PULL_SECRET__/d" "$2"
  fi

  if [ -n "$NODE_TYPE" ]; then
    sed -i -e "s|#__NODE_SELECTOR__||" "$2"
  else
    sed -i -e "/#__NODE_SELECTOR__/d" "$2"
  fi

  if [ "$STORAGE_TYPE" = "nfs" ]; then
    sed -i -e "s|#__STORAGE_PVC__||" -e "/#__STORAGE_EMPTYDIR__/d" "$2"
  else
    sed -i -e "s|#__STORAGE_EMPTYDIR__||" -e "/#__STORAGE_PVC__/d" "$2"
  fi

  if [ "$SERVICE_TYPE" = "ClusterIP" ]; then
    sed -i -e "/#__EXTERNAL_TRAFFIC_POLICY__/d" "$2"
  else
    sed -i -e "s|#__EXTERNAL_TRAFFIC_POLICY__||" "$2"
  fi

  # 機関別証明書の items: を差し込む (無ければマーカー行を消すだけ)
  if [ -s "$ITEMS_FILE" ]; then
    sed -i -e "/#__INSTITUTION_CERT_ITEMS__/r $ITEMS_FILE" \
           -e "/#__INSTITUTION_CERT_ITEMS__/d" "$2"
  else
    sed -i -e "/#__INSTITUTION_CERT_ITEMS__/d" "$2"
  fi
}

for file in "$TEMPLATE_DIR"/*.yaml; do
  base=$(basename "$file")

  # emptydir 運用では PV / PVC を作らない
  if [ "$STORAGE_TYPE" = "emptydir" ]; then
    case "$base" in
      volume-pv.yaml|volume-pvc.yaml) continue ;;
    esac
  fi

  # secret.yaml の中身は検証用ミドルウェアの PostgreSQL パスワードだけなので、
  # 共通ミドルウェアを使うときは作らない (使われない Secret にパスワードを残さない)
  if [ "$DEPLOY_MIDDLEWARE" != "true" ]; then
    case "$base" in
      secret.yaml) continue ;;
    esac
  fi

  render "$file" "$MANIFEST_DIR/$base"
done

if [ "$DEPLOY_MIDDLEWARE" = "true" ]; then
  render "$MIDDLEWARE_TEMPLATE_DIR/middleware.yaml" "$MANIFEST_DIR/middleware.yaml"
  echo "  ミドルウェア (検証用 PostgreSQL / Redis / RabbitMQ) も生成した"
fi

# 置換漏れの検出
if grep -rn '__[A-Z0-9_]*__' "$MANIFEST_DIR"; then
  echo "ERROR: 置換されていないプレースホルダが残っている" >&2
  exit 5
fi

# ------------------------------------------------------------
# server.config.toml
#
# リポジトリの configs/server.config.toml を唯一の正とし、環境依存の値だけを
# 上書きする (テンプレートを複製すると本体の設定追加に追従できないため)。
# [develop] セクションは本番へ持ち込まないよう丸ごと落とす。
# ------------------------------------------------------------
# Sentinel ノードの [[redis.sentinel.nodes]] ブロックを組み立てる。
# リポジトリの TOML には空の2件が置いてあるが、実際の台数に合わせて差し替える。
SENTINEL_BLOCK=""
for node in $REDIS_SENTINEL_NODES; do
  case "$node" in
    *:*) node_host=${node%:*}; node_port=${node##*:} ;;
    *)   node_host=$node;      node_port=26379 ;;
  esac
  case "$node_port" in
    ''|*[!0-9]*)
      echo "ERROR: REDIS_SENTINEL_NODES のポートが不正: $node" >&2
      exit 4 ;;
  esac
  SENTINEL_BLOCK="$SENTINEL_BLOCK$(printf '[[redis.sentinel.nodes]]\nhost = "%s"\nport = %s\n\n' \
    "$node_host" "$node_port")
"
done

awk -v vhost="$VHOST" \
    -v secret_key="$SECRET_KEY" \
    -v pg_user="$POSTGRES_USER" \
    -v pg_pass="$POSTGRES_PASSWORD" \
    -v pg_host="$POSTGRES_HOST" \
    -v pg_port="$POSTGRES_PORT" \
    -v pg_db="$POSTGRES_DB" \
    -v redis_cache_type="$REDIS_CACHE_TYPE" \
    -v redis_url="$REDIS_URL" \
    -v sentinel_master="$REDIS_SENTINEL_MASTER" \
    -v sentinel_block="$SENTINEL_BLOCK" \
    -v db_app_cache="$REDIS_DB_APP_CACHE" \
    -v db_account_store="$REDIS_DB_ACCOUNT_STORE" \
    -v db_result_backend="$REDIS_DB_RESULT_BACKEND" \
    -v db_group_cache="$REDIS_DB_GROUP_CACHE" \
    -v rabbitmq_url="$RABBITMQ_URL" \
    -v map_core="$MAP_CORE_BASE_URL" '
  # セクション追跡。
  #   [develop] / [[develop.accounts]] … 出力しない
  #   [[redis.sentinel.nodes]]         … 生成したブロックで置き換える
  /^\[/ {
    section = $0
    if (section ~ /^\[\[?develop/) {
      skip = 1
    } else if (section == "[[redis.sentinel.nodes]]" && sentinel_block != "") {
      skip = 1
      if (!nodes_emitted) {
        printf "%s", sentinel_block
        nodes_emitted = 1
      }
    } else {
      skip = 0
    }
  }
  skip { next }

  section == "" && /^server_name[[:space:]]*=/ { print "server_name = \"" vhost "\""; next }
  section == "" && /^secret_key[[:space:]]*=/  { print "secret_key = \"" secret_key "\""; next }

  section == "[sp]" && /^entity_id[[:space:]]*=/ {
    print "entity_id = \"https://" vhost "/shibboleth-sp\""; next
  }

  section == "[map_core]" && /^base_url[[:space:]]*=/ { print "base_url = \"" map_core "\""; next }

  section == "[postgres]" && /^user[[:space:]]*=/     { print "user = \"" pg_user "\""; next }
  section == "[postgres]" && /^password[[:space:]]*=/ { print "password = \"" pg_pass "\""; next }
  section == "[postgres]" && /^host[[:space:]]*=/     { print "host = \"" pg_host "\""; next }
  section == "[postgres]" && /^port[[:space:]]*=/     { print "port = " pg_port; next }
  section == "[postgres]" && /^db[[:space:]]*=/       { print "db = \"" pg_db "\""; next }

  section == "[redis]" && /^cache_type[[:space:]]*=/ {
    print "cache_type = \"" redis_cache_type "\""; next
  }

  section == "[redis.database]" && db_app_cache != "" && /^app_cache[[:space:]]*=/ {
    print "app_cache = " db_app_cache; next
  }
  section == "[redis.database]" && db_account_store != "" && /^account_store[[:space:]]*=/ {
    print "account_store = " db_account_store; next
  }
  section == "[redis.database]" && db_result_backend != "" && /^result_backend[[:space:]]*=/ {
    print "result_backend = " db_result_backend; next
  }
  section == "[redis.database]" && db_group_cache != "" && /^group_cache[[:space:]]*=/ {
    print "group_cache = " db_group_cache; next
  }

  section == "[redis.single]" && /^base_url[[:space:]]*=/ { print "base_url = \"" redis_url "\""; next }

  section == "[redis.sentinel]" && /^master_name[[:space:]]*=/ {
    print "master_name = \"" sentinel_master "\""; next
  }

  section == "[rabbitmq]" && /^url[[:space:]]*=/ { print "url = \"" rabbitmq_url "\""; next }

  { print }
' "$REPO_ROOT/configs/server.config.toml" > "$CONF_DIR/server.config.toml"

# 想定通り置換されたかを確認する (awk のマッチ漏れを黙って通さない)
assert_conf() {
  if ! grep -qF "$1" "$CONF_DIR/server.config.toml"; then
    echo "ERROR: server.config.toml に '$1' が入っていない" >&2
    exit 6
  fi
}

assert_conf "server_name = \"$VHOST\""
assert_conf "entity_id = \"https://$VHOST/shibboleth-sp\""
assert_conf "host = \"$POSTGRES_HOST\""
assert_conf "db = \"$POSTGRES_DB\""
assert_conf "url = \"$RABBITMQ_URL\""
assert_conf "base_url = \"$MAP_CORE_BASE_URL\""
assert_conf "cache_type = \"$REDIS_CACHE_TYPE\""
assert_conf "group_cache = $REDIS_DB_GROUP_CACHE"

if [ "$REDIS_CACHE_TYPE" = "RedisSentinelCache" ]; then
  assert_conf "master_name = \"$REDIS_SENTINEL_MASTER\""
  assert_conf "app_cache = $REDIS_DB_APP_CACHE"
  assert_conf "account_store = $REDIS_DB_ACCOUNT_STORE"
  assert_conf "result_backend = $REDIS_DB_RESULT_BACKEND"
  for node in $REDIS_SENTINEL_NODES; do
    case "$node" in
      *:*) node_host=${node%:*} ;;
      *)   node_host=$node ;;
    esac
    assert_conf "host = \"$node_host\""
  done
  # 空の [[redis.sentinel.nodes]] が残っていないこと
  if grep -q '^host = ""' "$CONF_DIR/server.config.toml"; then
    echo "ERROR: 空の [[redis.sentinel.nodes]] が残っている" >&2
    exit 6
  fi
else
  assert_conf "base_url = \"$REDIS_URL\""
fi

if grep -q '^\[\[\?develop' "$CONF_DIR/server.config.toml"; then
  echo "ERROR: server.config.toml から [develop] を落とせていない" >&2
  exit 6
fi

# ------------------------------------------------------------
# shibboleth2.xml
#
# nginx/shibboleth2.xml は entityID と RequestMapper の Host 名が
# localhost 固定なので、vhost に差し替えたものを ConfigMap にする。
# ------------------------------------------------------------
sed -e "s|entityID=\"https://localhost/shibboleth-sp\"|entityID=\"https://$VHOST/shibboleth-sp\"|" \
    -e "s|<Host name=\"localhost\"|<Host name=\"$VHOST\"|" \
    "$REPO_ROOT/nginx/shibboleth2.xml" > "$CONF_DIR/shibboleth2.xml"

for expected in \
  "entityID=\"https://$VHOST/shibboleth-sp\"" \
  "<Host name=\"$VHOST\"" ; do
  if ! grep -qF "$expected" "$CONF_DIR/shibboleth2.xml"; then
    echo "ERROR: shibboleth2.xml に '$expected' が入っていない" >&2
    exit 6
  fi
done

# ------------------------------------------------------------
# 証明書
# ------------------------------------------------------------
if [ -n "${TLS_CRT:-}" ] && [ -n "${TLS_KEY:-}" ]; then
  cp "$TLS_CRT" "$SSL_DIR/server.crt"
  cp "$TLS_KEY" "$SSL_DIR/server.key"
else
  echo "  TLS_CRT / TLS_KEY が未指定なので自己署名証明書を生成する (検証用)"
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -subj "/CN=$VHOST/O=$VHOST" \
    -addext "subjectAltName=DNS:$VHOST,DNS:localhost,IP:127.0.0.1" > /dev/null 2>&1
fi

if [ -n "${SP_CRT:-}" ] && [ -n "${SP_KEY:-}" ]; then
  cp "$SP_CRT" "$SP_DIR/server.crt"
  cp "$SP_KEY" "$SP_DIR/server.key"
else
  echo "  SP_CRT / SP_KEY が未指定なのでサーバ証明書を流用する"
  cp "$SSL_DIR/server.crt" "$SP_DIR/server.crt"
  cp "$SSL_DIR/server.key" "$SP_DIR/server.key"
fi

chmod 600 "$SSL_DIR/server.key" "$SP_DIR/server.key"

cp "$PARAMS_FILE" "$OUT/params.env"
# 生成物には秘密鍵・パスワードが入る
chmod -R go-rwx "$OUT"

echo ""
echo "generated: $OUT"
echo "  次に: ./deploy_jcgroups.sh $OUT"
