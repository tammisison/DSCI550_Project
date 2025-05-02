@echo off
echo Starting Docker services...
cd %~dp0
docker-compose up -d
echo Services are starting, please wait...
timeout /t 10
echo.
echo Solr is available at: http://localhost:8983/solr/
echo Elasticsearch is available at: http://localhost:9200/
echo.
echo To import data into Solr, run: import_data.bat
echo.
pause
