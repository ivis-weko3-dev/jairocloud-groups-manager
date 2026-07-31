#!/bin/sh
#
# 目的: k8s へデプロイするコンテナイメージを2つビルドする
#   1. アプリイメージ (uwsgi / celery / flask CLI 兼用)
#   2. nginx イメージ (nginx + Shibboleth SP + 静的 SPA)
#
# 引数
# 1. vhost    : 公開する FQDN。Nuxt の serverName としてイメージに焼き込まれる
# 2. registry : プッシュ先レジストリ (例 nrt.ocir.io/xxxxx/jcgroups)
# 3. tag      : イメージタグ
# 4. --push   : 指定するとビルド後に docker push する (任意)
#
# 例
#   ./build_images.sh groups.example.ac.jp nrt.ocir.io/nrbslpthdcco/jc 20260730 --push
#
# 【重要】nginx イメージは vhost ごとにビルドし直す必要がある。
# configs/app.config.ts の serverName は Nuxt のビルド時に静的 SPA へ
# インライン展開されるため、実行時に環境変数で差し替えられない。

set -e

if [ $# -lt 3 ]; then
  echo "usage : $0 vhost registry tag [--push]"
  exit 3
fi

VHOST=$1
REGISTRY=$2
TAG=$3
PUSH=${4:-}

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

APP_IMAGE="$REGISTRY/jc-groups-manager:$TAG"
NGINX_IMAGE="$REGISTRY/jc-groups-manager-nginx:$TAG"

# アプリイメージは `COPY . .` で configs/server.config.toml を焼き込む。
# 開発者ログインが有効な TOML を焼き込むと、その値がイメージに残る。
# 実行時は Secret でマウント上書きするので実害は出にくいが、
# 事故を防ぐためビルド前に弾く。
if grep -qE '^[[:space:]]*developer_login[[:space:]]*=[[:space:]]*true' \
     "$REPO_ROOT/configs/server.config.toml"; then
  echo "ERROR: configs/server.config.toml で developer_login = true になっている。" >&2
  echo "       このままイメージへ焼き込まれるため、コメントアウトしてからビルドすること。" >&2
  exit 5
fi

cd "$REPO_ROOT"

echo "=== build $APP_IMAGE ==="
docker build --target prod -t "$APP_IMAGE" .

echo "=== build $NGINX_IMAGE (serverName=$VHOST) ==="
docker build --target prod \
  -f nginx/Dockerfile \
  --build-arg "SERVER_NAME=$VHOST" \
  -t "$NGINX_IMAGE" .

# serverName が実際に焼き込まれたか、生成物を grep して確認する。
echo "=== verify serverName in the generated SPA ==="
docker run --rm --entrypoint sh "$NGINX_IMAGE" -c \
  "grep -rl '$VHOST' /usr/share/nginx/html/_nuxt/ | head -1" \
  || { echo "ERROR: serverName=$VHOST が静的 SPA に含まれていない" >&2; exit 6; }

if [ "$PUSH" = "--push" ]; then
  echo "=== push ==="
  docker push "$APP_IMAGE"
  docker push "$NGINX_IMAGE"
fi

echo ""
echo "APP_IMAGE   = $APP_IMAGE"
echo "NGINX_IMAGE = $NGINX_IMAGE"
