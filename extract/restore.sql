/*
  WWI 백업 복원. sqlcmd 변수 EDITION = Full | Standard

  docker exec wwi-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
    -v EDITION=Full -i /scripts/restore.sql

  논리 파일 이름이 다르다는 오류가 나면 아래 FILELISTONLY 결과를 보고 MOVE 절을 고칩니다.
*/
SET NOCOUNT ON;

RESTORE FILELISTONLY
FROM DISK = N'/var/opt/mssql/backup/WideWorldImporters-$(EDITION).bak';

IF '$(EDITION)' = 'Full'
    RESTORE DATABASE WideWorldImporters
    FROM DISK = N'/var/opt/mssql/backup/WideWorldImporters-Full.bak'
    WITH
        MOVE N'WWI_Primary'         TO N'/var/opt/mssql/data/WideWorldImporters.mdf',
        MOVE N'WWI_UserData'        TO N'/var/opt/mssql/data/WideWorldImporters_UserData.ndf',
        MOVE N'WWI_Log'             TO N'/var/opt/mssql/data/WideWorldImporters.ldf',
        MOVE N'WWI_InMemory_Data_1' TO N'/var/opt/mssql/data/WideWorldImporters_InMemory_Data_1',
        REPLACE, STATS = 10;
ELSE
    RESTORE DATABASE WideWorldImporters
    FROM DISK = N'/var/opt/mssql/backup/WideWorldImporters-Standard.bak'
    WITH
        MOVE N'WWI_Primary'  TO N'/var/opt/mssql/data/WideWorldImporters.mdf',
        MOVE N'WWI_UserData' TO N'/var/opt/mssql/data/WideWorldImporters_UserData.ndf',
        MOVE N'WWI_Log'      TO N'/var/opt/mssql/data/WideWorldImporters.ldf',
        REPLACE, STATS = 10;

SELECT name, state_desc, compatibility_level
FROM sys.databases
WHERE name = N'WideWorldImporters';
