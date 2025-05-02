# Haunted Places Data Visualization

## Overview
This project analyzes and visualizes haunted places data across the United States. It explores patterns in reported hauntings, types of apparitions, and correlations with geographic and temporal factors.

## Structure
- `Data/`: Contains the original TSV data file
- `json_data/`: JSON files for visualization
- `plots/`: Interactive HTML visualizations
- `thumbnails/`: Thumbnail images for visualizations
- `docker/`: Docker configuration and scripts for Solr and ElasticSearch
- `index.html`: Main project web page
- `geoparser_input.txt`: Processed data for MEMEX GeoParser

## How to Use
1. Open `index.html` in a web browser to view the project dashboard
2. Click on any visualization to explore it in detail
3. To use with Solr or ElasticSearch:
  - Navigate to the `docker` folder
  - Run `start_services.bat` (Windows) or `./start_services.sh` (Mac/Linux)
  - After services start, run `import_data.bat` or `./import_data.sh` to import data
4. For MEMEX tools integration, use the prepared data files with their respective applications

## Visualizations
1. **Map Visualization**: Geographic distribution of haunted places
2. **Timeline Visualization**: Historical trends of haunting reports
3. **Event Types Visualization**: Breakdown of paranormal event types
4. **Apparition Types Visualization**: Analysis of different apparition types
5. **State Heatmap**: State-level analysis of hauntings and evidence

## Requirements
- Python 3.7+
- Pandas
- Plotly
- Docker (for Solr and ElasticSearch)

## Team Information
Team Number: 12
