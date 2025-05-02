import os
import pandas as pd
import json
import re
import subprocess
import sys
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import shutil
import time

def load_and_clean_data(input_file):
    """Load and clean data"""
    print(f"Loading data file: {input_file}")
    try:
        # Read TSV file
        df = pd.read_csv(input_file, sep='\t')

        # Handle missing values
        df = df.fillna('')

        # Convert year to numeric
        df['year'] = pd.to_numeric(df['year'], errors='coerce')

        print(f"Successfully loaded data, total {len(df)} rows")
        return df
    except Exception as e:
        print(f"Error: Failed to load data - {str(e)}")
        return None


def create_output_directories(base_dir):
    """Create all required output directories"""
    directories = [
        os.path.join(base_dir, "json_data"),
        os.path.join(base_dir, "plots"),
        os.path.join(base_dir, "thumbnails"),
        os.path.join(base_dir, "docker")
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

    return directories


def process_data(df, output_dir):
    """Process data and create all summary files"""
    json_dir = os.path.join(output_dir, "json_data")

    # Create various summary data
    state_summary = create_state_summary(df, os.path.join(json_dir, "state_summary.json"))
    time_summary = create_time_summary(df, os.path.join(json_dir, "time_summary.json"))
    event_type_summary = create_event_type_summary(df, os.path.join(json_dir, "event_type_summary.json"))
    apparition_summary = create_apparition_summary(df, os.path.join(json_dir, "apparition_summary.json"))

    # Prepare external tools data
    prepare_for_solr(df, os.path.join(json_dir, "solr_import.json"))
    prepare_for_geoparser(df, os.path.join(output_dir, "geoparser_input.txt"))

    return {
        "state_summary": state_summary,
        "time_summary": time_summary,
        "event_type_summary": event_type_summary,
        "apparition_summary": apparition_summary
    }


def create_visualizations(df, summaries, output_dir):
    """Create all visualizations"""
    plots_dir = os.path.join(output_dir, "plots")

    # Create various visualizations
    create_map_visualization(df, os.path.join(plots_dir, "map_visualization.html"))
    create_timeline_visualization(summaries["time_summary"], os.path.join(plots_dir, "timeline_visualization.html"))
    create_event_type_visualization(summaries["event_type_summary"],
                                    os.path.join(plots_dir, "event_types_visualization.html"))
    create_apparition_type_visualization(summaries["apparition_summary"],
                                         os.path.join(plots_dir, "apparition_types_visualization.html"))
    create_state_heatmap(summaries["state_summary"], os.path.join(plots_dir, "state_heatmap.html"))


def setup_docker(output_dir):
    """Set up Docker configuration and provide startup scripts"""
    docker_dir = os.path.join(output_dir, "docker")

    # Create docker-compose.yml
    create_docker_compose(docker_dir)

    # Create startup scripts
    create_docker_startup_script(docker_dir)

    # Create data import scripts
    create_data_import_script(docker_dir, output_dir)


def create_project_files(output_dir, team_number):
    """Create project files (README, requirements.txt, etc.)"""
    create_index_html(output_dir)
    create_readme(output_dir)
    create_requirements(output_dir)
    create_thumbnails(os.path.join(output_dir, "plots"), os.path.join(output_dir, "thumbnails"))
    prepare_submission(output_dir, team_number)


# Below are implementations of various functions...

def create_state_summary(df, output_file):
    """Create state-level summary data"""
    try:
        # Group by state
        state_summary = df.groupby('state').agg({
            'city': 'count',
            'audio_evidence': lambda x: (x == True).sum(),
            'visual_evidence': lambda x: (x == True).sum(),
        }).reset_index()

        # Rename columns
        state_summary = state_summary.rename(columns={
            'city': 'haunt_count',
            'audio_evidence': 'audio_evidence_count',
            'visual_evidence': 'visual_evidence_count'
        })

        # Save as JSON
        state_summary.to_json(output_file, orient='records', indent=2)
        print(f"Created state-level summary data: {output_file}")

        return state_summary
    except Exception as e:
        print(f"Error: Failed to create state summary - {str(e)}")
        return pd.DataFrame()


def create_time_summary(df, output_file):
    """Create year-based summary data"""
    try:
        # Group by year
        time_summary = df.groupby('year').agg({
            'city': 'count',
            'witness_count': 'sum',
        }).reset_index()

        # Filter out missing years
        time_summary = time_summary.dropna(subset=['year'])

        # Save as JSON
        time_summary.to_json(output_file, orient='records', indent=2)
        print(f"Created time summary data: {output_file}")

        return time_summary
    except Exception as e:
        print(f"Error: Failed to create time summary - {str(e)}")
        return pd.DataFrame()


def create_event_type_summary(df, output_file):
    """Create event type summary data"""
    try:
        # Create a list to store all event types
        event_types = []

        # Extract event types (handle cases where each row might have multiple types)
        for event_type in df['event_type']:
            if isinstance(event_type, str) and event_type:
                # Split by comma or other delimiters
                types = [t.strip() for t in re.split(r'[,;]', event_type)]
                event_types.extend(types)

        # Calculate frequency
        event_counts = pd.Series(event_types).value_counts().reset_index()
        event_counts.columns = ['event_type', 'count']

        # Save as JSON
        event_counts.to_json(output_file, orient='records', indent=2)
        print(f"Created event type summary data: {output_file}")

        return event_counts
    except Exception as e:
        print(f"Error: Failed to create event type summary - {str(e)}")
        return pd.DataFrame()


def create_apparition_summary(df, output_file):
    """Create apparition type summary data"""
    try:
        # Create a list to store all apparition types
        apparition_types = []

        # Extract apparition types (handle cases where each row might have multiple types)
        for app_type in df['apparition_type']:
            if isinstance(app_type, str) and app_type:
                # Split by comma or other delimiters
                types = [t.strip() for t in re.split(r'[,;]', app_type)]
                apparition_types.extend(types)

        # Calculate frequency
        type_counts = pd.Series(apparition_types).value_counts().reset_index()
        type_counts.columns = ['apparition_type', 'count']

        # Save as JSON
        type_counts.to_json(output_file, orient='records', indent=2)
        print(f"Created apparition type summary data: {output_file}")

        return type_counts
    except Exception as e:
        print(f"Error: Failed to create apparition type summary - {str(e)}")
        return pd.DataFrame()


def prepare_for_solr(df, output_file):
    """Prepare Solr import data"""
    try:
        # Create dataframe copy
        solr_df = df.copy()

        # Convert column names to Solr-friendly format
        solr_df.columns = [col.replace('.', '_').replace(' ', '_').lower() for col in solr_df.columns]

        # Add unique ID field
        solr_df['id'] = ['haunted_' + str(i) for i in range(len(solr_df))]

        # Convert to JSON
        solr_df.to_json(output_file, orient='records', indent=2)
        print(f"Created Solr import file: {output_file}")
    except Exception as e:
        print(f"Error: Failed to prepare Solr data - {str(e)}")


def prepare_for_geoparser(df, output_file):
    """Prepare GeoParser import data"""
    try:
        # Select relevant columns
        geo_df = df[['city', 'state', 'description', 'location']].copy()

        # Combine location information
        geo_df['full_text'] = geo_df.apply(
            lambda row: f"{row['description']} Location: {row['city']}, {row['state']}, {row['location']}",
            axis=1
        )

        # Keep only full text column
        geo_text_df = geo_df[['full_text']].copy()

        # Write to text file (one entry per line)
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in geo_text_df['full_text']:
                f.write(f"{text}\n\n")

        print(f"Created GeoParser input file: {output_file}")
    except Exception as e:
        print(f"Error: Failed to prepare GeoParser data - {str(e)}")


def create_map_visualization(df, output_file):
    """Create map visualization"""
    try:
        # Filter valid latitude/longitude data
        geo_df = df.copy()

        # Convert to numeric
        geo_df['latitude'] = pd.to_numeric(geo_df['latitude'], errors='coerce')
        geo_df['longitude'] = pd.to_numeric(geo_df['longitude'], errors='coerce')

        # Filter out rows with missing coordinates
        geo_df = geo_df.dropna(subset=['latitude', 'longitude'])

        # Create hover text for each row
        geo_df['hover_text'] = geo_df.apply(
            lambda row: f"<b>{row['city']}, {row['state']}</b><br>" +
                        f"Type: {row['apparition_type']}<br>" +
                        f"Event: {row['event_type']}<br>" +
                        f"{str(row['description'])[:200]}...",
            axis=1
        )

        # Create color mapping for apparition types
        color_map = {
            'Ghost': 'red',
            'Misty Figure': 'pink',
            'Demonic Entity': 'darkred',
            'Celestial Being': 'blue',
            'Unknown': 'gray'
        }

        # Create color column
        geo_df['marker_color'] = 'gray'  # Default color

        # Assign colors by apparition type
        for key, color in color_map.items():
            mask = geo_df['apparition_type'].astype(str).str.contains(key, na=False)
            geo_df.loc[mask, 'marker_color'] = color

        # Create map
        fig = px.scatter_mapbox(
            geo_df,
            lat="latitude",
            lon="longitude",
            hover_name="city",
            hover_data=["state", "apparition_type", "event_type"],
            color="marker_color",
            color_discrete_map="identity",
            zoom=3,
            height=800,
            title="Haunted Places Across the United States"
        )

        # Use open street map
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

        # Save to file
        fig.write_html(output_file)
        print(f"Created map visualization: {output_file}")
    except Exception as e:
        print(f"Error: Failed to create map visualization - {str(e)}")


def create_timeline_visualization(time_df, output_file):
    """Create timeline visualization"""
    try:
        # Filter valid years
        time_df = time_df[(time_df['year'] >= 1800) & (time_df['year'] <= 2025)].copy()

        # Create two subplots
        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=("Haunted Places Reports by Year",
                                            "Witness Count by Year"))

        # Add report count line chart
        fig.add_trace(
            go.Scatter(
                x=time_df['year'],
                y=time_df['city'],
                mode='lines+markers',
                name='Reports',
                line=dict(color='royalblue', width=2),
                marker=dict(size=8)
            ),
            row=1, col=1
        )

        # Add witness count line chart
        fig.add_trace(
            go.Scatter(
                x=time_df['year'],
                y=time_df['witness_count'],
                mode='lines+markers',
                name='Witnesses',
                line=dict(color='firebrick', width=2),
                marker=dict(size=8)
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode="x unified"
        )

        # Update x and y axes
        fig.update_xaxes(title_text="Year", row=2, col=1)
        fig.update_yaxes(title_text="Number of Reports", row=1, col=1)
        fig.update_yaxes(title_text="Number of Witnesses", row=2, col=1)

        # Save to file
        fig.write_html(output_file)
        print(f"Created timeline visualization: {output_file}")
    except Exception as e:
        print(f"Error: Failed to create timeline visualization - {str(e)}")


def create_event_type_visualization(event_df, output_file):
    """Create event type visualization"""
    try:
        # Limit to top 10 categories
        if len(event_df) > 10:
            event_df = event_df.sort_values('count', ascending=False).head(10)

        # Create pie chart
        fig = px.pie(
            event_df,
            values='count',
            names='event_type',
            title='Haunted Places by Event Type',
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.3
        )

        # Update layout
        fig.update_layout(
            legend_title="Event Type",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )

        # Update labels
        fig.update_traces(textposition='inside', textinfo='percent+label')

        # Save to file
        fig.write_html(output_file)
        print(f"Created event type visualization: {output_file}")
    except Exception as e:
        print(f"Error: Failed to create event type visualization - {str(e)}")


def create_apparition_type_visualization(type_df, output_file):
    """Create apparition type visualization"""
    try:
        # Limit to top 10 categories
        if len(type_df) > 10:
            type_df = type_df.sort_values('count', ascending=False).head(10)

        # Create horizontal bar chart
        fig = px.bar(
            type_df,
            x='count',
            y='apparition_type',
            orientation='h',
            title='Apparition Types in Haunted Places',
            color='count',
            color_continuous_scale='Viridis'
        )

        # Update layout
        fig.update_layout(
            xaxis_title="Number of Reports",
            yaxis_title="Apparition Type",
            yaxis=dict(autorange="reversed")  # Sort from top to bottom by count
        )

        # Save to file
        fig.write_html(output_file)
        print(f"Created apparition type visualization: {output_file}")
    except Exception as e:
        print(f"Error: Failed to create apparition type visualization - {str(e)}")


def create_state_heatmap(state_df, output_file):
    """Create state-level heatmap"""
    try:
        # Create three subplots
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=("Haunting Count by State", "Audio Evidence by State", "Visual Evidence by State"),
            specs=[[{"type": "choropleth"}, {"type": "choropleth"}, {"type": "choropleth"}]]
        )

        # Add haunting count heatmap
        fig.add_trace(
            go.Choropleth(
                locations=state_df['state'],
                z=state_df['haunt_count'],
                locationmode='USA-states',
                colorscale='Reds',
                colorbar_title="Count",
                colorbar=dict(len=0.75, x=0.15),
                name="Haunt Count"
            ),
            row=1, col=1
        )

        # Add audio evidence heatmap
        fig.add_trace(
            go.Choropleth(
                locations=state_df['state'],
                z=state_df['audio_evidence_count'],
                locationmode='USA-states',
                colorscale='Blues',
                colorbar_title="Audio",
                colorbar=dict(len=0.75, x=0.5),
                name="Audio Evidence"
            ),
            row=1, col=2
        )

        # Add visual evidence heatmap
        fig.add_trace(
            go.Choropleth(
                locations=state_df['state'],
                z=state_df['visual_evidence_count'],
                locationmode='USA-states',
                colorscale='Greens',
                colorbar_title="Visual",
                colorbar=dict(len=0.75, x=0.85),
                name="Visual Evidence"
            ),
            row=1, col=3
        )

        # Update layout
        fig.update_layout(
            title_text="Haunted Places Analysis by State",
            geo=dict(
                scope='usa',
                projection=go.layout.geo.Projection(type='albers usa'),
                showlakes=True,
                lakecolor='rgb(255, 255, 255)'
            ),
            width=1200,
            height=600
        )

        # Save to file
        fig.write_html(output_file)
        print(f"Created state-level heatmap: {output_file}")
    except Exception as e:
        print(f"Error: Failed to create state heatmap - {str(e)}")


def create_docker_compose(docker_dir):
    """Create Docker Compose configuration file"""
    try:
        docker_compose = """version: '3'

services:
  solr:
    image: solr:latest
    ports:
      - "8983:8983"
    volumes:
      - solr_data:/var/solr
    command:
      - solr-precreate
      - haunted_places

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

volumes:
  solr_data:
  es_data:
"""

        # Write docker-compose.yml
        with open(os.path.join(docker_dir, "docker-compose.yml"), "w") as f:
            f.write(docker_compose)

        print(f"Created Docker configuration file: {os.path.join(docker_dir, 'docker-compose.yml')}")
    except Exception as e:
        print(f"Error: Failed to create Docker configuration file - {str(e)}")


def create_docker_startup_script(docker_dir):
    """Create Docker startup scripts"""
    # Windows batch file
    batch_script = """@echo off
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
"""

    # Linux/Mac shell script
    shell_script = """#!/bin/bash
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
"""

    # Write startup scripts
    with open(os.path.join(docker_dir, "start_services.bat"), "w") as f:
        f.write(batch_script)

    with open(os.path.join(docker_dir, "start_services.sh"), "w") as f:
        f.write(shell_script)

    # Set execution permissions for Linux/Mac script
    try:
        os.chmod(os.path.join(docker_dir, "start_services.sh"), 0o755)
    except:
        pass

    print(
        f"Created Docker startup scripts: {os.path.join(docker_dir, 'start_services.bat')} and {os.path.join(docker_dir, 'start_services.sh')}")


def create_data_import_script(docker_dir, output_dir):
    """Create data import scripts"""
    # Get relative path
    rel_path = os.path.relpath(os.path.join(output_dir, "json_data", "solr_import.json"), docker_dir)

    # Windows batch file
    batch_script = f"""@echo off
echo Importing data into Solr...
cd %~dp0
docker exec -it $(docker ps -q -f name=solr) post -c haunted_places {rel_path}
echo Data import complete.
pause
"""

    # Linux/Mac shell script
    shell_script = f"""#!/bin/bash
echo "Importing data into Solr..."
cd "$(dirname "$0")"
docker exec -it $(docker ps -q -f name=solr) post -c haunted_places {rel_path}
echo "Data import complete."
read -p "Press Enter to continue..."
"""

    # Write import scripts
    with open(os.path.join(docker_dir, "import_data.bat"), "w") as f:
        f.write(batch_script)

    with open(os.path.join(docker_dir, "import_data.sh"), "w") as f:
        f.write(shell_script)

    # Set execution permissions for Linux/Mac script
    try:
        os.chmod(os.path.join(docker_dir, "import_data.sh"), 0o755)
    except:
        pass

    print(
        f"Created data import scripts: {os.path.join(docker_dir, 'import_data.bat')} and {os.path.join(docker_dir, 'import_data.sh')}")


def create_index_html(output_dir):
    """Create main HTML file"""
    try:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>Multimodal Haunted Places Data Analysis</title>
   <style>
       body {
           font-family: Arial, sans-serif;
           margin: 0;
           padding: 0;
           background-color: #f5f5f5;
       }
       header {
           background-color: #333;
           color: white;
           padding: 20px;
           text-align: center;
       }
       .container {
           max-width: 1200px;
           margin: 0 auto;
           padding: 20px;
       }
       .section {
           margin-bottom: 40px;
           background-color: white;
           padding: 20px;
           border-radius: 8px;
           box-shadow: 0 2px 4px rgba(0,0,0,0.1);
       }
       h1, h2, h3 {
           color: #333;
       }
       .viz-grid {
           display: grid;
           grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
           gap: 20px;
           margin-top: 20px;
       }
       .viz-item {
           background-color: #f9f9f9;
           border-radius: 8px;
           overflow: hidden;
           transition: transform 0.3s;
           box-shadow: 0 2px 4px rgba(0,0,0,0.1);
       }
       .viz-item:hover {
           transform: translateY(-5px);
           box-shadow: 0 4px 8px rgba(0,0,0,0.2);
       }
       .viz-item img {
           width: 100%;
           height: 200px;
           object-fit: cover;
           background-color: #eee;
       }
       .viz-item .content {
           padding: 15px;
       }
       a {
           text-decoration: none;
           color: #0066cc;
       }
       a:hover {
           text-decoration: underline;
       }
       footer {
           background-color: #333;
           color: white;
           text-align: center;
           padding: 20px;
           margin-top: 40px;
       }
       .instructions {
           background-color: #e6f7ff;
           border-left: 4px solid #1890ff;
           padding: 15px;
           margin: 20px 0;
       }
   </style>
</head>
<body>
   <header>
       <h1>Multimodal Haunted Places Data Analysis</h1>
       <p>Interactive visualizations of haunted places across the United States</p>
   </header>

   <div class="container">
       <div class="section">
           <h2>Project Overview</h2>
           <p>This project analyzes haunted places data across the United States, exploring patterns in reported hauntings, types of apparitions, and correlations with geographic and temporal factors. The visualizations provide interactive ways to explore the data and discover insights about paranormal phenomena.</p>

           <div class="instructions">
               <h3>How to Use This Project</h3>
               <ol>
                   <li>Browse the visualizations below by clicking on any of the cards</li>
                   <li>To set up the docker environment for Solr and ElasticSearch:
                       <ul>
                           <li>Go to the <code>docker</code> folder</li>
                           <li>Run <code>start_services.bat</code> (Windows) or <code>./start_services.sh</code> (Mac/Linux)</li>
                           <li>After services start, run <code>import_data.bat</code> or <code>./import_data.sh</code> to import data</li>
                       </ul>
                   </li>
                   <li>For MEMEX GeoParser, use the <code>geoparser_input.txt</code> file with the GeoParser application</li>
               </ol>
           </div>
       </div>

       <div class="section">
           <h2>Explore Visualizations</h2>
           <div class="viz-grid">
               <div class="viz-item">
                   <img src="thumbnails/map.png" alt="Map Visualization">
                   <div class="content">
                       <h3>Haunted Places Map</h3>
                       <p>Interactive map showing the geographic distribution of haunted places across the United States.</p>
                       <a href="plots/map_visualization.html" target="_blank">View Visualization</a>
                   </div>
               </div>

               <div class="viz-item">
                   <img src="thumbnails/timeline.png" alt="Timeline Visualization">
                   <div class="content">
                       <h3>Historical Timeline</h3>
                       <p>Explore how haunting reports have changed over time and the number of witnesses.</p>
                       <a href="plots/timeline_visualization.html" target="_blank">View Visualization</a>
                   </div>
               </div>

               <div class="viz-item">
                   <img src="thumbnails/event_types.png" alt="Event Types Visualization">
                   <div class="content">
                       <h3>Event Types</h3>
                       <p>Breakdown of different types of paranormal events and their frequency.</p>
                       <a href="plots/event_types_visualization.html" target="_blank">View Visualization</a>
                   </div>
               </div>

               <div class="viz-item">
                   <img src="thumbnails/apparition_types.png" alt="Apparition Types Visualization">
                   <div class="content">
                       <h3>Apparition Types</h3>
                       <p>Analysis of different kinds of apparitions reported in haunted places.</p>
                       <a href="plots/apparition_types_visualization.html" target="_blank">View Visualization</a>
                   </div>
               </div>

               <div class="viz-item">
                   <img src="thumbnails/heatmap.png" alt="State Heatmap">
                   <div class="content">
                       <h3>State-Level Analysis</h3>
                       <p>Heatmap showing haunting density and evidence types by state.</p>
                       <a href="plots/state_heatmap.html" target="_blank">View Visualization</a>
                   </div>
               </div>
           </div>
       </div>

       <div class="section">
           <h2>External Tools</h2>
           <p>This project also integrates with the following MEMEX tools:</p>
           <ul>
               <li><strong>MEMEX ImageSpace</strong> - For exploring similarities between haunted place images</li>
               <li><strong>MEMEX GeoParser</strong> - For extracting and visualizing geographic information</li>
           </ul>
           <p>Data from this project has been prepared for these tools and can be accessed in the output directory.</p>
       </div>
   </div>

   <footer>
       <p>Created for DSCI 550: Data Science at Scale - Spring 2025</p>
   </footer>
</body>
</html>
       """

        # Write HTML file
        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Created index HTML file: {os.path.join(output_dir, 'index.html')}")

        # Create thumbnails directory
        thumbnails_dir = os.path.join(output_dir, "thumbnails")
        os.makedirs(thumbnails_dir, exist_ok=True)

        # Create a simple placeholder PNG
        create_placeholder_image(thumbnails_dir)
    except Exception as e:
        print(f"Error creating index HTML file: {str(e)}")


def create_placeholder_image(thumbnails_dir):
    """Create placeholder images"""
    # Create placeholders for each visualization
    placeholders = {
        "map.png": "Map Visualization",
        "timeline.png": "Timeline Visualization",
        "event_types.png": "Event Types",
        "apparition_types.png": "Apparition Types",
        "heatmap.png": "State Heatmap"
    }

    # Try to use matplotlib to create placeholder images
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        for filename, title in placeholders.items():
            plt.figure(figsize=(6, 4))
            plt.text(0.5, 0.5, title, ha='center', va='center', fontsize=14)
            plt.axis('off')
            plt.savefig(os.path.join(thumbnails_dir, filename), dpi=100, bbox_inches='tight')
            plt.close()
            print(f"Created thumbnail: {filename}")
    except:
        # If matplotlib is not available, create a simple placeholder file
        placeholder_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

        for filename in placeholders.keys():
            with open(os.path.join(thumbnails_dir, filename), "wb") as f:
                f.write(placeholder_content)
            print(f"Created simple placeholder thumbnail: {filename}")


def create_readme(output_dir):
    """Create README file"""
    readme_content = """# Haunted Places Data Visualization

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
"""

    # Write README file
    with open(os.path.join(output_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Created README file: {os.path.join(output_dir, 'README.txt')}")


def create_requirements(output_dir):
    """Create requirements.txt file"""
    requirements_content = """pandas>=1.3.0
plotly>=5.3.0
numpy>=1.20.0
matplotlib>=3.4.0
"""

    # Write requirements.txt file
    with open(os.path.join(output_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(requirements_content)

    print(f"Created requirements.txt file: {os.path.join(output_dir, 'requirements.txt')}")


def create_thumbnails(plots_dir, thumbnails_dir):
    """Create thumbnails (simplified version)"""
    os.makedirs(thumbnails_dir, exist_ok=True)

    # Try to use Selenium to create actual thumbnails
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time

        print("Trying to create visualization thumbnails using Selenium...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1200,800")

        driver = webdriver.Chrome(options=chrome_options)

        html_files = {
            "map_visualization.html": "map.png",
            "timeline_visualization.html": "timeline.png",
            "event_types_visualization.html": "event_types.png",
            "apparition_types_visualization.html": "apparition_types.png",
            "state_heatmap.html": "heatmap.png"
        }

        for html_file, png_file in html_files.items():
            file_path = os.path.join(plots_dir, html_file)
            if os.path.exists(file_path):
                try:
                    driver.get('file:///' + os.path.abspath(file_path))
                    time.sleep(2)  # Wait for loading
                    driver.save_screenshot(os.path.join(thumbnails_dir, png_file))
                    print(f"Created thumbnail: {png_file}")
                except Exception as e:
                    print(f"Error creating thumbnail for {html_file}: {str(e)}")

        driver.quit()
    except:
        print("Selenium not available or thumbnail creation failed. Using placeholder images instead.")
        create_placeholder_image(thumbnails_dir)


def prepare_submission(output_dir, team_number):
    """Prepare final submission files"""
    try:
        # Create submission directory
        submission_dir = f"TEAM_{team_number}_DSCI550_HW_DATAVIS"
        os.makedirs(submission_dir, exist_ok=True)

        # Create subdirectories
        os.makedirs(os.path.join(submission_dir, "Data"), exist_ok=True)
        os.makedirs(os.path.join(submission_dir, "Source Code"), exist_ok=True)
        os.makedirs(os.path.join(submission_dir, "script"), exist_ok=True)

        # Copy README.txt
        shutil.copy(
            os.path.join(output_dir, "README.txt"),
            os.path.join(submission_dir, "Readme.txt")
        )

        # Copy requirements.txt
        shutil.copy(
            os.path.join(output_dir, "requirements.txt"),
            os.path.join(submission_dir, "Requirements.txt")
        )

        # Copy current script to Source Code directory
        script_path = os.path.abspath(sys.argv[0])
        if os.path.exists(script_path):
            shutil.copy(
                script_path,
                os.path.join(submission_dir, "Source Code", os.path.basename(script_path))
            )

        print(f"Prepared submission directory: {submission_dir}")
        print("Please add your report as TEAM_12_DATAVIS.pdf")
    except Exception as e:
        print(f"Error preparing submission files: {str(e)}")


def run_docker_services():
    """Try to start Docker services"""
    try:
        # Check if Docker is installed
        try:
            subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE)
        except:
            print("Warning: Docker is not installed or not in PATH. Cannot automatically start Docker services.")
            return False

        # Check if docker-compose is installed
        try:
            subprocess.run(["docker-compose", "--version"], check=True, stdout=subprocess.PIPE)
        except:
            print(
                "Warning: Docker Compose is not installed or not in PATH. Cannot automatically start Docker services.")
            return False

        # Start Docker services
        print("Starting Docker services...")
        subprocess.run(["docker-compose", "up", "-d"], cwd="docker")
        print("Docker services started. Solr is available at http://localhost:8983/solr/")
        print("ElasticSearch is available at http://localhost:9200/")
        return True
    except Exception as e:
        print(f"Error starting Docker services: {str(e)}")
        return False


def main():
    """Main function"""
    print("=== Haunted Places Data Visualization Project ===")

    # Get team number
    team_number = input("Please enter team number (e.g., 01): ").strip() or "XX"

    # Get input file path
    default_path = "/data_3/data_3/final_haunted_analysis.tsv"
    input_file = input(f"Please enter TSV file path (default: {default_path}): ").strip() or default_path

    # Set output directory
    output_dir = input("Please enter output directory (default: output_data): ").strip() or "output_data"

    print("\nStarting processing...")

    # Step 1: Load data
    df = load_and_clean_data(input_file)
    if df is None:
        print("Error: Unable to load data. Please check file path and format.")
        return

    # Step 2: Create output directories
    create_output_directories(output_dir)

    # Step 3: Process data
    print("\n--- Processing Data ---")
    summaries = process_data(df, output_dir)

    # Step 4: Create visualizations
    print("\n--- Creating Visualizations ---")
    create_visualizations(df, summaries, output_dir)

    # Step 5: Setup Docker
    print("\n--- Setting Up Docker Environment ---")
    setup_docker(output_dir)

    # Step 6: Create project files
    print("\n--- Creating Project Files ---")
    create_project_files(output_dir, team_number)

    # Step 7: Ask whether to start Docker services
    print("\nProject files have been generated!")
    start_docker = input("Start Docker services? (y/n): ").strip().lower()
    if start_docker == 'y':
        run_docker_services()

    print("\n=== Processing Complete ===")
    print(f"Project output directory: {output_dir}")
    print(f"Please open {os.path.join(output_dir, 'index.html')} to view the visualization project")


if __name__ == "__main__":
    main()