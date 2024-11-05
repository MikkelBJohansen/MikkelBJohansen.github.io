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

    lemma_counts = df_filtered.groupby(['lemma', 'pos', 'token_text']).size().reset_index(name='count')

    # Generate top 50 occurrences data tables grouped by lemma and token_text
    top_50_results = {}
    for category in pos_category_filter:
        category_df = lemma_counts[lemma_counts['pos'] == category]
        top_50_grouped = category_df.groupby(['lemma', 'token_text']).agg({'count': 'sum'}).reset_index()
        top_50_sorted = top_50_grouped.groupby('lemma').agg({'count': 'sum'}).reset_index()
        top_50_sorted = top_50_sorted.sort_values(by='count', ascending=False).head(50)
        top_50_results[category] = top_50_grouped[top_50_grouped['lemma'].isin(top_50_sorted['lemma'])]

    # Generate HTML for Data Tables
    table_html = ''
    for category, result_df in top_50_results.items():
        table_html += f"<h3>Top 50 occurrences for POS category '{category}':</h3>"
        table_html += result_df.to_html(index=False, classes='data-table')

    # Plotting Separate Charts for Each POS with Plotly for Interactivity
    combined_pos_filter = ['VERB', 'AUX']
    other_pos_filter = ['NOUN', 'ADP', 'ADV']

    # Plotting Combined Chart for VERB and AUX
    combined_df = lemma_counts[lemma_counts['pos'].isin(combined_pos_filter)]
    combined_grouped = combined_df.groupby(['lemma', 'token_text']).agg({'count': 'sum'}).reset_index()
    top_lemmas_combined = combined_grouped.groupby('lemma')['count'].sum().sort_values(ascending=False).head(15).index
    combined_grouped = combined_grouped[combined_grouped['lemma'].isin(top_lemmas_combined)]

    # Create figure for combined VERB and AUX chart
    fig_combined = go.Figure()

    # Add bars for each lemma with subdivisions by token_text
    for lemma in top_lemmas_combined:
        lemma_df = combined_grouped[combined_grouped['lemma'] == lemma]
        fig_combined.add_trace(
            go.Bar(
                x=[lemma] * len(lemma_df),
                y=lemma_df['count'],
                name=lemma,
                text=lemma_df['token_text'],
                hoverinfo='x+y+text',
                marker=dict(line=dict(width=1, color='black'))
            )
        )

    # Set the layout properties for the combined chart
    fig_combined.update_layout(
        title='Frequency Trends of Top Lemmas for POS Categories: VERB and AUX',
        xaxis_title='Lemma',
        yaxis_title='Total Count of Lemma Occurrences',
        barmode='stack',
        plot_bgcolor='#f0f0f0',
        paper_bgcolor='#f8f8f8',
        font=dict(size=14),
        xaxis_tickangle=-45,
        legend_title_text='Lemmas',
        height=700,
        margin=dict(t=80, b=150, l=50, r=50),
    )

    # Adding watermark to the plot using annotation
    fig_combined.add_annotation(
        text="Mikkel Barner Johansen",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=40, color="lightgray"),
        opacity=0.2,
        align="center"
    )

    # Generate HTML for the combined chart
    combined_chart_html = fig_combined.to_html(full_html=False, include_plotlyjs='cdn')
    table_html += f"<h3>Chart for POS categories 'VERB' and 'AUX':</h3>"
    table_html += combined_chart_html

    # Plotting Separate Charts for NOUN, ADP, ADV
    for pos in other_pos_filter:
        pos_df = lemma_counts[lemma_counts['pos'] == pos]
        pos_grouped = pos_df.groupby(['lemma', 'token_text']).agg({'count': 'sum'}).reset_index()
        top_lemmas = pos_grouped.groupby('lemma')['count'].sum().sort_values(ascending=False).head(15).index
        pos_grouped = pos_grouped[pos_grouped['lemma'].isin(top_lemmas)]

        # Create figure for each POS category
        fig = go.Figure()

        # Add bars for each lemma with subdivisions by token_text
        for lemma in top_lemmas:
            lemma_df = pos_grouped[pos_grouped['lemma'] == lemma]
            fig.add_trace(
                go.Bar(
                    x=[lemma] * len(lemma_df),
                    y=lemma_df['count'],
                    name=lemma,
                    text=lemma_df['token_text'],
                    hoverinfo='x+y+text',
                    marker=dict(line=dict(width=1, color='black'))
                )
            )

        # Set the layout properties for each chart
        fig.update_layout(
            title=f'Frequency Trends of Top Lemmas for POS Category: {pos}',
            xaxis_title='Lemma',
            yaxis_title='Total Count of Lemma Occurrences',
            barmode='stack',
            plot_bgcolor='#f0f0f0',
            paper_bgcolor='#f8f8f8',
            font=dict(size=14),
            xaxis_tickangle=-45,
            legend_title_text='Lemmas',
            height=700,
            margin=dict(t=80, b=150, l=50, r=50),
        )

        # Adding watermark to the plot using annotation
        fig.add_annotation(
            text="Mikkel Barner Johansen",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=40, color="lightgray"),
            opacity=0.2,
            align="center"
        )

        # Generate HTML for the chart
        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

        # Append the chart HTML to the main HTML content
        table_html += f"<h3>Chart for POS category '{pos}':</h3>"
        table_html += chart_html

    # Define the path to index.html
    index_html_path = '/home/pi/danish_data_project/index.html'

    # Read the existing HTML file
    with open(index_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Replace the placeholders with the generated content
    html_content = html_content.replace('<!--DYNAMIC_SECTION_CHART-->', table_html)

    # Write the updated HTML content back to the file
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Log success message and print to terminal
    success_message = "Successfully updated index.html with new charts and tables."
    logging.info(success_message)
    print(success_message)

    # Call the auto_commit.sh script
    subprocess.run(['/home/pi/danish_data_project/auto_commit.sh'])

except Exception as e:
    logging.exception("An error occurred during execution.")
