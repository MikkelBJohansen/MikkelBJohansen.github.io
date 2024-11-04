import sqlite3 as sq
import pandas as pd
import plotly.graph_objects as go
import subprocess
import logging
import os
import sys

# Set up logging
log_file = '/home/pi/danish_data_project/error_log.txt'
logging.basicConfig(filename=log_file, level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

try:
    # Updated SQLite connection string to use the /home/pi/database directory
    conn = sq.connect('/home/pi/danish_data.sqlite3')

    query = "SELECT * FROM tokens"

    # Load data into DataFrame
    df = pd.read_sql_query(query, conn)

    # Filter data
    pos_category_filter = ['NOUN', 'VERB', 'AUX', 'ADP', 'ADV']
    df_filtered = df[df['pos'].isin(pos_category_filter)]

    lemma_counts = df_filtered.groupby(['lemma', 'pos']).size().reset_index(name='count')

    top_50_results = {}
    for category in pos_category_filter:
        category_df = lemma_counts[lemma_counts['pos'] == category]
        top_50_results[category] = category_df.sort_values(by='count', ascending=False).head(50)

    # Generate HTML for Data Tables
    table_html = ''
    for category, result_df in top_50_results.items():
        table_html += f"<h3>Top 50 occurrences for POS category '{category}':</h3>"
        table_html += result_df.to_html(index=False, classes='data-table')

    # Plotting the Combined Charts with Plotly for Interactivity
    # Prepare data for plotting
    df_plot = lemma_counts.groupby(['lemma', 'pos'])['count'].sum().unstack(fill_value=0)
    top_lemmas = df_plot.sum(axis=1).sort_values(ascending=False).head(50).index
    df_plot = df_plot.loc[top_lemmas]

    # Create the figure for the bar plot
    fig_all_time = go.Figure()

    # Add bars for each POS category
    for pos in pos_category_filter:
        if pos in df_plot.columns:
            fig_all_time.add_trace(
                go.Bar(
                    x=df_plot.index,
                    y=df_plot[pos],
                    name=pos,
                    hoverinfo='x+y+name',
                    marker=dict(line=dict(width=1, color='black'))
                )
            )

    # Set the layout properties
    fig_all_time.update_layout(
        title='Combined Frequency Trends of Top Lemmas - All Time',
        xaxis_title='Lemma',
        yaxis_title='Total Count of Lemma Occurrences',
        barmode='stack',
        plot_bgcolor='#f0f0f0',
        paper_bgcolor='#f8f8f8',
        font=dict(size=14),
        xaxis_tickangle=-45,
        legend_title_text='POS Category',
        height=700,
        margin=dict(t=80, b=150, l=50, r=50),
    )

    # Adding watermark to the plot using annotation
    fig_all_time.add_annotation(
        text="Mikkel Barner Johansen",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=40, color="lightgray"),
        opacity=0.2,
        align="center"
    )

    # Generate HTML for the chart
    chart_html = fig_all_time.to_html(full_html=False, include_plotlyjs='cdn')

    # Define the path to index.html
    index_html_path = '/home/pi/danish_data_project/index.html'

    # Read the existing HTML file
    with open(index_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Replace the placeholders with the generated content
    html_content = html_content.replace('<!--DYNAMIC_SECTION_CHART-->', chart_html)
    html_content = html_content.replace('<!--DYNAMIC_SECTION_TABLE-->', table_html)

    # Write the updated HTML content back to the file
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Call the auto_commit.sh script
    subprocess.run(['/home/pi/danish_data_project/auto_commit.sh'])

except Exception as e:
    logging.exception("An error occurred during execution.")
