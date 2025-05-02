#!/bin/bash
echo "Importing data into Solr..."
cd "$(dirname "$0")"
docker exec -it $(docker ps -q -f name=solr) post -c haunted_places ../json_data/solr_import.json
echo "Data import complete."
read -p "Press Enter to continue..."
