@echo off
echo Importing data into Solr...
cd %~dp0
docker exec -it $(docker ps -q -f name=solr) post -c haunted_places ../json_data/solr_import.json
echo Data import complete.
pause
