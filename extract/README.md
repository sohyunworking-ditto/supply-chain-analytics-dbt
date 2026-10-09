# extract: WWI → Parquet (1회)

Microsoft의 Wide World Importers 샘플 DB를 SQL Server 컨테이너에 복원하고, 분석 대상 테이블을 `data/raw/*.parquet`로 추출합니다. 추출이 끝나면 컨테이너는 필요 없습니다.

## 준비

- **Docker Desktop:**
  - Apple Silicon이면 Settings → General에서 **Use Rosetta for x86_64/amd64 emulation**을 켭니다.
  - Resources에서 메모리를 4GB 이상 할당합니다.
- **Python 3.12:** pymssql과 dbt가 3.14를 아직 지원하지 않을 수 있어 3.12를 씁니다.

```bash
brew install python@3.12
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp extract/.env.example extract/.env      # 암호 바꾸기
```

## 실행

```bash
# 1) 백업 받기 (약 120MB)
./extract/download_bak.sh

# 2) SQL Server 기동 (처음엔 이미지 받느라 수 분)
docker compose -f extract/docker-compose.yml --env-file extract/.env up -d
docker compose -f extract/docker-compose.yml ps     # STATUS가 healthy가 될 때까지 대기

# 3) 복원
docker exec wwi-mssql bash -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -v EDITION=Full -i /scripts/restore.sql'

# 4) 확인 쿼리 (기간, 이력 변경 수, 발주-입고 연결)
docker exec wwi-mssql bash -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -d WideWorldImporters -i /scripts/checks.sql -W -s "|"'

# 5) 추출
python extract/extract.py

# 6) 정리
docker compose -f extract/docker-compose.yml down       # 복원한 DB까지 지우려면 -v
```

## 막힐 때

| 증상 | 대응 |
|---|---|
| 컨테이너가 바로 종료됨 | `docker logs wwi-mssql`로 원인을 봅니다. 암호 정책 위반이나 메모리 부족이 흔합니다 |
| Full 복원 실패 (In-Memory 관련 오류) | `./extract/download_bak.sh Standard` 후 `-v EDITION=Standard`로 다시 복원 |
| 논리 파일 이름 오류 | `restore.sql`이 먼저 출력하는 FILELISTONLY 결과의 LogicalName으로 MOVE 절을 고칩니다 |
| `pip install pymssql` 실패 | Python 3.12 가상환경인지 확인합니다. 그래도 안 되면 `brew install freetds` 후 재설치 |
