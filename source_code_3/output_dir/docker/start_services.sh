#!/bin/bash
echo "Starting Docker services..."
cd "$(dirname "$0")"
docker-compose up -d
echo "Services are starting, please wait..."
sleep 10
echo ""
echo "Solr is available at: http://localhost:8983/solr/"
echo "Elasticsearch is available at: http://localhost:9200/"
echo ""
echo "To import data into Solr, run: ./import_data.sh"
echo ""
read -p "Press Enter to continue..."
