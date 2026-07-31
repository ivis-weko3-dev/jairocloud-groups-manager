# Kubernetes デプロイ

JAIRO Cloud Groups Manager を k8s で動かすためのイメージビルド手順とマニフェスト。
構成・命名・スクリプトの流儀は `weko-k8s` の web デプロイ
(`deploy/weko/manifest_template/deploy-web.yaml` + `scripts/make_weko_manifests.sh`
+ `scripts/deploy_weko.sh`) に合わせてある。

```
k8s/
├── deploy/
│   ├── jcgroups/
│   │   ├── manifest_template/     __PLACEHOLDER__ 入りのマニフェスト
│   │   │   ├── namespace.yaml
│   │   │   ├── configmap.yaml
│   │   │   ├── secret.yaml
│   │   │   ├── deploy-web.yaml    nginx + web + worker (1 Pod 3 コンテナ)
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── volume-pv.yaml
│   │   │   ├── volume-pvc.yaml
│   │   │   └── job-db-init.yaml
│   │   └── params.env.example     環境ごとのパラメータ (これをコピーして使う)
│   └── middleware/
│       └── manifest_template/
│           └── middleware.yaml    検証用 PostgreSQL / Redis / RabbitMQ
└── scripts/
    ├── build_images.sh            イメージ2種のビルド (+ push)
    ├── make_jcgroups_manifests.sh params.env → 実マニフェスト生成
    ├── deploy_jcgroups.sh         生成物を kubectl apply
    └── delete_jcgroups.sh         リソース削除
```

## 構成

```
                     Ingress (TLS 終端 / backend-protocol: HTTPS)
                                   │ 443
  ┌────────────────────────────────▼─────────────────────────────────┐
  │ Deployment: <domain>-web        Service: <domain>-nginx (443/80) │
  │ ┌──────────────────────┐ ┌────────────────┐ ┌──────────────────┐ │
  │ │ nginx                │ │ web            │ │ worker           │ │
  │ │  nginx + shibd       │ │  uwsgi         │ │  celery          │ │
  │ │  + shibauthorizer    │─▶│  :5050        │ │                  │ │
  │ │  + shibresponder     │ │  (Flask API)   │ │                  │ │
  │ │  + 静的 SPA          │ └────────────────┘ └──────────────────┘ │
  │ └──────────────────────┘   hostAliases: web → 127.0.0.1          │
  └──────────────────────────────────┬───────────────────────────────┘
                                     │
        ┌────────────┬───────────────┴───────────────┬──────────────┐
        │            │                               │              │
  ┌─────▼──────┐┌────▼───────────┐┌─────────────────▼────┐┌────────▼─────────┐
  │ pgpool     ││ weko-rabbitmq  ││ weko-sentinel-service ││ 共有ストレージ    │
  │ .weko3pg   ││ .weko3ra       ││ .weko3re → redis      ││ /var/tmp/jcgroups │
  │ DB:jcgroups││ vhost:jcgroups ││ db 割当 + db4         ││ (NFS RWX)         │
  └────────────┘└────────────────┘└──────────┬───────────┘└──────────────────┘
        JAIRO Cloud 共通ミドルウェア (別 Namespace)  │ db4
                                                   └──▶ WEKO も同じ db4 を読む
```

weko と同じく **nginx / web / worker を1つの Pod に同居させている**。理由:

- `nginx` / `shibd` / `shibauthorizer` / `shibresponder` は Unix ドメインソケット
  (`/opt/shibboleth/*.sock`) で通信するため、そもそも 1 コンテナに同居が必須
  (`nginx/supervisord.conf`)。
- nginx イメージには `upstream api_server { server web:5050; }` が焼き込まれている
  (`nginx/conf.d/default.conf`)。同居させて `hostAliases` で `web` を
  `127.0.0.1` に向ければ、nginx が起動時に解決した ClusterIP をキャッシュし続ける
  問題 (Pod 入れ替え後に 502) を避けられる。アプリ用の Service は作っていない。

`web` と `worker` は同じイメージで `command` だけ差し替える
(`compose.prod.yaml` と同じ方針)。

## 手順

### 1. イメージをビルドする

```bash
cd k8s/scripts
./build_images.sh <FQDN> <レジストリ> <タグ> [--push]

# 例
./build_images.sh groups.example.ac.jp nrt.ocir.io/xxxxxxxx/jc 20260730 --push
```

作られるイメージ:

| イメージ | 中身 | 起動するもの |
|---|---|---|
| `<registry>/jc-groups-manager:<tag>` | Python / Flask (`Dockerfile` の prod ステージ) | uwsgi, celery, `flask db` |
| `<registry>/jc-groups-manager-nginx:<tag>` | nginx + Shibboleth SP + 静的 SPA (`nginx/Dockerfile` の prod ステージ) | supervisord |

**nginx イメージは FQDN ごとにビルドし直す必要がある。**
`configs/app.config.ts` の `serverName` は Nuxt のビルド時に静的 SPA へ
インライン展開されるため、実行時に環境変数で差し替えられない
(ビルド済みバンドルに `const zd="localhost", No=\`https://${zd}\`` の形で残る)。
`build_images.sh` は `--build-arg SERVER_NAME=<FQDN>` を渡してこれを注入し、
生成物を grep して実際に入ったかを確認する。
1 イメージを全環境で使い回したいなら `serverName` を `runtimeConfig` へ移す改修が必要。

またアプリイメージは `COPY . .` で `configs/server.config.toml` を焼き込むため、
`developer_login = true` のままビルドしようとすると `build_images.sh` が止める。
実行時には Secret でマウント上書きするので、イメージ内の TOML は
プレースホルダのままにしておくこと。

### 2. ミドルウェアを用意する

PostgreSQL / Redis / RabbitMQ は **JAIRO Cloud 共通のクラスタ (weko-k8s) を使う**。
`params.env.example` の既定値はその前提になっている。

| ミドルウェア | 接続先 | 実体 (weko-k8s) |
|---|---|---|
| PostgreSQL | `pgpool.weko3pg:5432` | Zalando postgres-operator + pgpool (`deploy/postgresql`) |
| Redis | `weko-sentinel-service.weko3re:26379` (master `mymaster`) | Redis + Sentinel (`deploy/redis`) |
| RabbitMQ | `weko-rabbitmq.weko3ra:5672` | RabbitMQ Cluster Operator (`deploy/rabbitmq`) |

いずれも別 Namespace なので `<service>.<namespace>` の DNS で引く。
weko3pg / weko3re / weko3ra には NetworkPolicy が無いので、Namespace をまたいだ
接続はそのまま通る。

#### PostgreSQL: ロールを作る

DB 自体は db-init Job の `flask db init` (`sqlalchemy_utils.create_database`) が作るので、
**ロールを CREATEDB 権限付きで用意しておけばよい**。pgpool 越しは md5 認証。

```bash
PG=$(kubectl get pod -n weko3pg -l application=spilo,spilo-role=master -o name | head -1)
kubectl exec -n weko3pg $PG -- psql -U postgres -c \
  "CREATE ROLE jcgroups WITH LOGIN CREATEDB PASSWORD '<POSTGRES_PASSWORD>';"
```

既存の `invenio` ロール (`postgresql-infrastructure-roles` の ConfigMap で
`createdb` 付き) を使い回すこともできるが、権限分離のため専用ロールを推奨。

#### RabbitMQ: vhost を作る

WEKO は機関ごとに vhost を切っている (`scripts/make_rabbitmq_vhost.sh`)。
同じ流儀で jcgroups 用の vhost を作り、使うユーザに権限を与える。

```bash
RA=$(kubectl get pod -n weko3ra -l app.kubernetes.io/name=weko-rabbitmq -o name | head -1)
kubectl exec -n weko3ra $RA -- rabbitmqctl add_vhost jcgroups
kubectl exec -n weko3ra $RA -- rabbitmqctl set_permissions -p jcgroups invenio ".*" ".*" ".*"
```

`RABBITMQ_URL` の末尾が vhost 名になる (`.../5672/jcgroups`)。
`//` で終わらせると既定 vhost `/` の意味になるので注意。

#### Redis: DB 番号を確保する

共通 Redis は 1 インスタンスを全機関で共有する構成 (`databases 40000`)。
**空いている DB 番号を運用側で確保してから `params.env` に書く。**
共通クラスタで既に決まっている番号:

| DB 番号 | 用途 |
|---|---|
| 機関ごとに払い出し | WEKO の `CACHE_REDIS_DB` / `ACCOUNTS_SESSION_REDIS_DB_NO` / `CELERY_RESULT_BACKEND_DB_NO` (`repositories.txt` の 16〜18 列目) |
| 3 | `CRAWLER_REDIS_DB` (固定) |
| 4 | `GROUP_INFO_REDIS_DB` (固定) |

jcgroups 側は `REDIS_DB_APP_CACHE` / `REDIS_DB_ACCOUNT_STORE` /
`REDIS_DB_RESULT_BACKEND` に空き番号を指定する。`RedisSentinelCache` のときは
この3つを明示しないと `make_jcgroups_manifests.sh` が止まる (リポジトリ既定値の
0/1/2 を黙って使うと機関の DB とぶつかるため)。

**`REDIS_DB_GROUP_CACHE` は 4 のまま変えない。** WEKO の
`GROUP_INFO_REDIS_DB = 4` が固定で、ここが WEKO との唯一の実行時結合点。

Sentinel ノードは headless Service を1件書けばよい (全 Sentinel Pod の IP が
引ける)。WEKO の `instance.cfg` も
`CACHE_REDIS_SENTINELS = [("weko-sentinel-service.weko3re","26379")]` と同じ書き方。

#### 検証用に自前のミドルウェアを立てる場合

`DEPLOY_MIDDLEWARE=true` にすると単一インスタンスの PostgreSQL / Redis / RabbitMQ を
同じ Namespace に立てる。そのときは接続先も併せて変える:

```
POSTGRES_HOST=postgres
REDIS_CACHE_TYPE=RedisCache
REDIS_URL=redis://redis:6379
REDIS_DB_APP_CACHE=0        # 単体 Redis なので既定値のままでよい
REDIS_DB_ACCOUNT_STORE=1
REDIS_DB_RESULT_BACKEND=2
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672//
```

### 3. パラメータを用意する

```bash
cp ../deploy/jcgroups/params.env.example /path/to/params.env
vi /path/to/params.env
```

FQDN・イメージ・レプリカ数・ストレージ・ミドルウェア接続先・証明書のパスを書く。
`params.env` は `.gitignore` 済み。

### 4. マニフェストを生成する

```bash
./make_jcgroups_manifests.sh /path/to/params.env /path/to/generated
```

```
/path/to/generated/<FQDN>/
├── manifests/*.yaml           __PLACEHOLDER__ を置換したマニフェスト
├── conf/server.config.toml    環境用に書き換えたアプリ設定
├── conf/shibboleth2.xml       entityID / Host を FQDN に置換したもの
├── ssl/server.crt|key         nginx / Shibboleth SP のサーバ証明書
├── sp/server.crt|key          mAP Core 接続用クライアント証明書
├── institutions/<FQDN>/...    機関別クライアント証明書
└── params.env                 使ったパラメータの控え
```

`server.config.toml` と `shibboleth2.xml` は**テンプレートを複製せず、リポジトリの
`configs/server.config.toml` / `nginx/shibboleth2.xml` を唯一の正として環境依存の値
だけを上書きする**。設定項目が増えても追従漏れが起きない。生成時に
`[develop]` セクションは丸ごと落とし、置換結果を assert している。

**生成物には `secret_key`・DB パスワード・秘密鍵が入る。Git に入れないこと。**

### 5. デプロイする

```bash
./deploy_jcgroups.sh /path/to/generated/<FQDN>

# 2回目以降 (DB 初期化 Job を流さない)
./deploy_jcgroups.sh /path/to/generated/<FQDN> --skip-db-init
```

やること:

1. Namespace 作成
2. ファイル由来の Secret / ConfigMap を `kubectl create ... | kubectl apply -f -` で作成
   (中身が Git に載らないようマニフェスト化していない)
3. ConfigMap / Secret / PV / PVC / Service / Ingress を apply
4. `DEPLOY_MIDDLEWARE=true` なら検証用ミドルウェアも apply して Ready 待ち
5. DB 初期化 Job (`flask db init && flask db create`) を流して完了待ち
6. `deploy-web.yaml` を apply して `rollout status` 待ち

削除は `./delete_jcgroups.sh /path/to/generated/<FQDN> [--all]`。
`--all` を付けると Namespace / PV / PVC も消える (データが消える)。

## 作られる Secret / ConfigMap

`<domain>` は FQDN の `.` `_` を `-` に置換したもの (weko-k8s と同じ流儀)。
例: `groups.example.ac.jp` → `groups-example-ac-jp`

| 名前 | 中身 | 作られ方 |
|---|---|---|
| `<domain>-secret` | `server.config.toml` | deploy スクリプトが `conf/` から作る |
| `<domain>-tls` | nginx / SP のサーバ証明書 | deploy スクリプトが `ssl/` から作る |
| `<domain>-cert` | Ingress 用 TLS Secret | deploy スクリプトが `ssl/` から作る |
| `<domain>-sp-cert` | mAP Core 接続用クライアント証明書 | deploy スクリプトが `sp/` から作る |
| `<domain>-institution-certs` | 機関別クライアント証明書 | deploy スクリプトが `institutions/` から作る |
| `<domain>-middleware` | PostgreSQL のパスワード | `secret.yaml` |
| `<domain>-configmap` | TZ / FLASK_ENV などの環境変数 | `configmap.yaml` |
| `<domain>-shibboleth2` | `shibboleth2.xml` | deploy スクリプトが `conf/` から作る |

**アプリ設定は環境変数で上書きできない。** `src/server/config.py` に env 読み込み機構が
ないため、接続先・シークレットはすべて `server.config.toml` 経由になる。
`<domain>-configmap` に置けるのは Flask / Python / OS レベルの環境変数だけ。

機関別クライアント証明書は `weko-group-cache-db` が
`/var/mnt/<FQDN>/server.crt|key` を読む (`loader.py:213-214`)。
Secret のキー名に `/` は使えないので、`make_jcgroups_manifests.sh` が
`INSTITUTION_CERTS_DIR` の中身から `items[].path` を生成して
サブディレクトリを組み立てる (キー名は `<FQDN>.server.crt`)。

## テンプレートの書き方

`__PLACEHOLDER__` は `make_jcgroups_manifests.sh` の `render()` が sed で置換する。
加えて**マーカー行**という仕組みがある:

```yaml
      #__NODE_SELECTOR__nodeSelector:
      #__NODE_SELECTOR__  nodeType: __NODE_TYPE__
```

条件を満たすときはマーカー文字列だけを削って有効化し、満たさないときは行ごと削除する。
`params.env` の値で出力を切り替えるのに使っている。

| マーカー | 制御するもの | 有効になる条件 |
|---|---|---|
| `#__IMAGE_PULL_SECRET__` | `imagePullSecrets` | `IMAGE_PULL_SECRET_NAME` が非空 |
| `#__NODE_SELECTOR__` | `nodeSelector` | `NODE_TYPE` が非空 |
| `#__STORAGE_PVC__` | 共有ストレージを PVC にする | `STORAGE_TYPE=nfs` |
| `#__STORAGE_EMPTYDIR__` | 共有ストレージを emptyDir にする | `STORAGE_TYPE=emptydir` |
| `#__EXTERNAL_TRAFFIC_POLICY__` | `externalTrafficPolicy: Local` | `SERVICE_TYPE` が ClusterIP 以外 |
| `#__INSTITUTION_CERT_ITEMS__` | 機関別証明書の `items:` | `INSTITUTION_CERTS_DIR` が非空 |

生成後に `__[A-Z0-9_]*__` が残っていないかを grep して、置換漏れなら失敗させる。

## 設計上の注意

### `enableServiceLinks: false` は必須

k8s は Namespace 内の Service ごとに Docker link 互換の環境変数を注入する。
Service 名 `redis` に対して `REDIS_PORT=tcp://<ClusterIP>:6379` が入り、
`weko-group-cache-db` の設定フィールド `REDIS_PORT` (pydantic-settings が
環境変数から読む) と衝突して**起動に失敗する**。

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for RuntimeConfig
cache_groups.redis_port
  Input should be a valid integer, unable to parse string as an integer
  [type=int_parsing, input_value='tcp://10.96.201.60:6379', input_type=str]
```

`POSTGRES_PORT` / `RABBITMQ_PORT` も同様に注入されるため、Service 名を変えるのでは
なく注入自体を止める。全 Pod spec に入れてある。

注入されるのは**同一 Namespace の Service だけ**なので、共通ミドルウェア
(別 Namespace) を使う構成では実際には衝突しない。ただし
`DEPLOY_MIDDLEWARE=true` で `redis` / `postgres` / `rabbitmq` を同じ Namespace に
立てた瞬間に再発するため、設定は外さないこと。

### TLS は SP に HTTPS で届ける

Shibboleth SP は `handlerSSL="true"` / `cookieProps="https"` で動くため、Ingress で
TLS を落として HTTP で Pod に渡すと SP のハンドラが動かない。
`ingress.yaml` は weko と同じく `nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"`
で Pod に対して張り直す。TLS ごと素通しさせたい場合は
`SERVICE_TYPE=LoadBalancer` で 443 を直接公開するか、ingress-nginx の
ssl-passthrough を使う (その場合クライアントに見せる証明書は `<domain>-tls` の方)。

### Celery の並列数を必ず明示する

`supervisord.worker.conf` の `celery -A server.celery_app worker` には
`--concurrency` 指定がない。Celery はノードの CPU 数だけ prefork するため、
CPU limit を付けてもコア数分 (検証環境では 64) fork してメモリを食い潰す。
`deploy-web.yaml` は `CELERY_CONCURRENCY` を明示的に渡している。

### supervisord は nginx コンテナだけ

アプリイメージの prod ステージは `USER root` のまま supervisord が pyuser に降格する
構造。k8s では 1 コンテナ 1 プロセスが素直なので、`web` は `uwsgi --ini`、
`worker` は `celery ... worker` を直接 `command` で起動し、`runAsUser: 1000` で
非 root 実行にしている。nginx コンテナだけは shibd との同居のため supervisord のまま。

### 共有ストレージ

`/var/tmp/jcgroups` (`[storage.local]` の `temporary` / `storage`) は web が
アップロードした CSV を worker が読むため両者に見せる必要がある。
1 Pod 同居なので `REPLICAS=1` なら `STORAGE_TYPE=emptydir` で足りるが、
複数レプリカでは Pod をまたいで同じ物が見えないといけないので
`STORAGE_TYPE=nfs` (ReadWriteMany) を使う。RWX を用意できない場合は
`server.config.toml` の `[storage] type` を `object_storage` に切り替える。

RWX を提供しない StorageClass では PVC が Pending のまま Pod が起動しない
(例: kind の既定 StorageClass は `NodePath only supports ReadWriteOnce ...` で失敗)。

### ヘルスチェック用エンドポイントがない

アプリにも nginx conf にも `/healthz` 相当がない。現状は
nginx は `GET /` (静的 index.html)、web は 5050 の tcpSocket、
worker は `celery inspect ping` で代替している。
nginx conf に `location /healthz { return 200; }` を足すのが本来は望ましい。

### ミドルウェアは JAIRO Cloud 共通クラスタを使う

接続先と事前準備は「手順 2」を参照。ここでは設計上の含意だけ。

- **DB / vhost / Redis DB 番号は共有資源**。jcgroups 専用に確保してから使う。
  特に Redis は機関ごとに DB 番号が払い出されているので、空き番号の管理が必要。
- **アプリ側に接続先を切り替える口は `server.config.toml` しかない**
  (`src/server/config.py` に env 読み込み機構がない)。接続先を変えるときは
  `params.env` を直して `make` → `deploy` をやり直し、`CONFIG_REVISION` を
  上げて Pod を rollout させる。
- `deploy/middleware/manifest_template/middleware.yaml` は
  `DEPLOY_MIDDLEWARE=true` のときだけ使う**検証用の単一インスタンス構成**。
  こちらは単体 Redis なので `REDIS_CACHE_TYPE=RedisCache` に変えること。

### WEKO との結合点

実行時に WEKO と共有するのは **Redis db4 のグループキャッシュのみ**。

| 項目 | 値 |
|---|---|
| Redis DB | `redis.database.group_cache` = 4 (`REDIS_DB_GROUP_CACHE`) |
| キー | `<FQDN の . と - を _ に置換>_gakunin_groups` |
| 値 | Hash: `updated_at` (ISO8601), `groups` (カンマ区切りのグループID) |
| 書き込み | Celery task `update_task()` (`src/server/services/group_caches.py:188`) |
| 読み出し | WEKO の `GROUP_INFO_REDIS_DB = 4` (`instance.cfg`) |

`src/server/datastore.py:61` の実装上、`app_cache` / `account_store` /
`result_backend` / `group_cache` は**すべて同じ `[redis]` 設定から生成される**
(DB 番号だけが違う)。共通 Redis を使う構成ではこれが都合よく働き、
`group_cache` が WEKO と同じインスタンスの db4 を指す。

逆に言うと、**jcgroups のキャッシュだけ別の Redis に置くことはできない**。
将来 jcgroups 専用 Redis に移すなら、`config.py` に group_cache 専用の接続先設定を
追加する改修が必要。

## 検証済みの内容

kind (k8s v1.34) で `STORAGE_TYPE=emptydir` / `REPLICAS=1` として実デプロイして確認した。

### 共通構成

| 項目 | 結果 |
|---|---|
| `build_images.sh` でイメージ2種のビルド | 成功 (serverName の焼き込み確認まで) |
| `make_jcgroups_manifests.sh` の置換 | 置換漏れなし・TOML / XML の assert 通過 |
| 生成された `server.config.toml` | `tomllib` でパースして値を確認 |
| 本番相当パラメータ (NFS / pull secret / nodeSelector / LoadBalancer / replicas=2 / 機関別証明書2件) のスキーマ検証 | `kubectl apply --dry-run=server --validate=strict` 通過 |
| db-init Job | Completed |
| Pod 起動 | nginx / web / worker の 3/3 Running |
| `GET /` (静的 SPA) / `GET /_nuxt/*.js` | 200 |
| `GET /api/auth/check` (nginx → hostAliases → uwsgi) | 401 `E401` (未認証として正しい応答) |
| `GET /api/dev/accounts` | 404 (prod では dev blueprint 未登録 = 正しい) |
| `GET /Shibboleth.sso/Metadata` | 200 (shibd 稼働) |
| web → worker のファイル共有 (`/var/tmp/jcgroups`) | 疎通 |
| 非 root 実行 (`runAsUser: 1000`) | uwsgi / celery とも正常動作 |
| `delete_jcgroups.sh` → `deploy_jcgroups.sh --skip-db-init` | 既存 DB を保持して再デプロイ成功 |

### 共通ミドルウェア構成 (`DEPLOY_MIDDLEWARE=false`)

JAIRO Cloud 共通クラスタと同じ形 (Service 名 / Namespace / Sentinel / headless
Service / `databases 40000`) を kind 上に模擬して確認した。

| 項目 | 結果 |
|---|---|
| PostgreSQL ロール作成 → `flask db init` で DB 作成 | `jcgroups` DB が owner=jcgroups で作られ、4 テーブル生成 |
| クロス Namespace 接続 (`pgpool.weko3pg` / `weko-rabbitmq.weko3ra` / `weko-sentinel-service.weko3re`) | すべて疎通 |
| RabbitMQ の専用 vhost | `Connected to amqp://invenio:**@weko-rabbitmq.weko3ra:5672/jcgroups` |
| Sentinel 経由の Redis 接続 (`RedisSentinelCache`, master `mymaster`) | 接続警告なし・read/write 成功 |
| Redis DB 番号の割り当て | `app_cache=100` / `account_store=101` / `group_cache=4` が実際に使われることを Redis 側の keyspace で確認 |
| DB 番号の未指定 / 重複 / Sentinel ノード未指定 | いずれも `make_jcgroups_manifests.sh` が停止 |

未検証: mAP Core (`sptest.cg.gakunin.jp`) への到達を要する機能、
Shibboleth 実 IdP との SAML 認証、Ingress コントローラ経由の疎通
(kind では Service への port-forward で確認)、NFS RWX PVC での複数レプリカ運用、
実際の共通クラスタ (pgpool の md5 認証・Sentinel 複数台でのフェイルオーバ) への接続。
