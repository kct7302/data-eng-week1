# data-eng-week1

Docker Compose를 활용한 다중 컨테이너 구성 실습


## 1. 실습 환경

| 항목 | 구성 |
|---|---|
| 실행 도구 | Docker, Docker Compose |
| 데이터베이스 이미지 | `postgres:16` |
| 데이터베이스 관리 도구 이미지 | `dpage/pgadmin4:9.18` |
| 애플리케이션 빌드 경로 | `./app` |
| 데이터베이스 이름 | `pipeline` |
| 데이터베이스 사용자 | `engineer` |
| Docker / Compose 버전 | [작성 필요] |

사용한 도구의 버전은 다음 명령어로 확인한다.

```bash
docker --version
docker compose version
```

## 2. 산출물 구성

| 파일 또는 경로 | 역할 |
|---|---|
| `docker-compose.yml` | 서비스, 이미지, 환경 변수, 포트, 볼륨 정의 |
| `app/` | 애플리케이션 이미지 빌드에 사용하는 디렉터리 |
| `README.md` | 실습 목적, 구성, 실행 방법 정리 |

서비스별 설정은 다음과 같다.

| 서비스 | 역할 | 주요 설정 |
|---|---|---|
| `db` | PostgreSQL 데이터베이스 | 호스트 `5432` → 컨테이너 `5432` |
| `admin` | pgAdmin 웹 관리 도구 | 호스트 `8081` → 컨테이너 `80` |
| `app` | 실습용 애플리케이션 | `./app` 경로에서 이미지 빌드 |

`db`에는 `pgdata` 볼륨을 연결했으며, 컨테이너 내부의 `/var/lib/postgresql/data` 경로에 데이터가 저장되도록 구성했다.

## 3. 실습 과정과 실행 방법

### ① 서비스 구성

`docker-compose.yml`에 세 개의 서비스를 정의했다.

- `db`: 환경 변수로 데이터베이스 계정과 데이터베이스 이름을 지정했다.
- `admin`: pgAdmin 로그인 계정을 지정하고, 브라우저에서 접속할 수 있도록 포트를 연결했다.
- `app`: `build: ./app`으로 애플리케이션 이미지의 빌드 경로를 지정했다.
- `admin`과 `app`: `depends_on`에 `db`를 지정했다.

### ② 이미지 빌드 및 컨테이너 실행

Docker가 실행 중이고 `app/`에 빌드에 필요한 Dockerfile과 소스가 준비된 상태에서, `docker-compose.yml`이 있는 폴더에서 실행한다.

```bash
docker compose up -d --build
```

- `--build`: 애플리케이션 이미지를 빌드한다.
- `-d`: 컨테이너를 백그라운드에서 실행한다.

### ③ 컨테이너 상태 및 로그 확인

```bash
docker compose ps -a
docker compose logs db
docker compose logs app
```

컨테이너 상태와 로그를 통해 데이터베이스 및 애플리케이션의 실행 결과를 확인한다.

### ④ pgAdmin 접속 및 데이터베이스 연결

브라우저에서 [pgAdmin 접속 주소](http://localhost:8081)를 연다.

- 로그인 이메일: `admin@example.com`
- 로그인 비밀번호: Compose 파일의 `PGADMIN_DEFAULT_PASSWORD` 값

로그인 후 서버를 등록할 때 다음 정보를 입력한다.

| 항목 | 입력값 |
|---|---|
| 서버 표시 이름 | `pipeline-db` 등 원하는 이름 |
| Host name/address | `db` |
| Port | `5432` |
| Maintenance database | `pipeline` |
| Username | `engineer` |
| Password | Compose 파일의 `POSTGRES_PASSWORD` 값 |

pgAdmin 컨테이너에서 PostgreSQL에 연결할 때는 서비스 이름인 `db`를 호스트로 사용한다. Compose의 기본 네트워크에서는 서비스 이름으로 다른 컨테이너에 접근할 수 있다. [Docker 공식 문서](https://docs.docker.com/compose/how-tos/networking/)

### ⑤ 데이터베이스 확인

다음 명령어로 접속한 데이터베이스와 사용자를 확인한다.

```bash
docker compose exec db psql -U engineer -d pipeline -c "SELECT current_database();"
```

설정대로 초기화된 데이터베이스에 접속했다면 다음 값이 반환되는지 확인한다.

| 항목 | 예상값 |
|---|---|
| `current_database` | `pipeline` |


### ⑥ 실습 종료

```bash
docker compose down
```

