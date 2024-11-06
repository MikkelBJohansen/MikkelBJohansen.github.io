import sqlite3 as sq
import pandas as pd
import plotly.graph_objects as go
import subprocess
import logging
import os
import sys
from datetime import datetime, timedelta

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

    # Ensure 'datetime' column exists before converting
    if 'datetime' in df_filtered.columns:
        df_filtered['datetime'] = pd.to_datetime(df_filtered['datetime'])
    else:
        raise KeyError("The 'datetime' column is missing from the dataset.")

    # Separate data for the current week
    one_week_ago = datetime.now() - timedelta(days=7)
    df_week = df_filtered[df_filtered['datetime'] >= one_week_ago]

    # Group the data by lemma, pos, and token_text
    lemma_counts = df_filtered.groupby(['lemma', 'pos', 'token_text']).size().reset_index(name='count')
    lemma_counts_week = df_week.groupby(['lemma', 'pos', 'token_text']).size().reset_index(name='count')

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
        table_html += result_df.to_html(index=False, classes='data-table', border=0)

    # Plotting Separate Charts for Each POS with Plotly for Interactivity
    combined_pos_filter = ['VERB', 'AUX']
    other_pos_filter = ['NOUN', 'ADP', 'ADV']

    def create_chart(df, pos_filter, title_suffix):
        grouped_df = df[df['pos'].isin(pos_filter)].groupby(['lemma', 'token_text']).agg({'count': 'sum'}).reset_index()
        top_lemmas = grouped_df.groupby('lemma')['count'].sum().sort_values(ascending=False).head(15).index
        grouped_df = grouped_df[grouped_df['lemma'].isin(top_lemmas)]

        fig = go.Figure()

        for lemma in top_lemmas:
            lemma_df = grouped_df[grouped_df['lemma'] == lemma]
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

        fig.update_layout(
            title=f'Frequency Trends of Top Lemmas for POS Categories: {title_suffix}',
            xaxis_title='Lemma',
            yaxis_title='Total Count of Lemma Occurrences',
            barmode='stack',
            plot_bgcolor='#2b2b2b',
            paper_bgcolor='#1e1e1e',
            font=dict(size=14, color='white'),
            xaxis_tickangle=-45,
            legend_title_text='Lemmas',
            height=700,
            margin=dict(t=80, b=150, l=50, r=50),
            title_x=0.5,
        )

        for trace in fig.data:
            trace.textposition = 'outside'

        fig.add_annotation(
            text="Mikkel Barner Johansen",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=40, color="lightgray"),
            opacity=0.2,
            align="center"
        )

        return fig

    # Create and combine charts for all time and weekly data
    combined_chart_html = ""

    # Combined VERB and AUX charts
    fig_combined_all_time = create_chart(lemma_counts, combined_pos_filter, 'VERB and AUX (All Time)')
    fig_combined_week = create_chart(lemma_counts_week, combined_pos_filter, 'VERB and AUX (This Week)')
    combined_chart_html += "<div style='display: flex; justify-content: space-around;'>"
    combined_chart_html += f"<div>{fig_combined_all_time.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    combined_chart_html += f"<div>{fig_combined_week.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    combined_chart_html += "</div>"

    # Charts for NOUN, ADP, ADV
    for pos in other_pos_filter:
        fig_all_time = create_chart(lemma_counts, [pos], f'{pos} (All Time)')
        fig_week = create_chart(lemma_counts_week, [pos], f'{pos} (This Week)')
        combined_chart_html += f"<h3>Charts for POS category '{pos}':</h3>"
        combined_chart_html += "<div style='display: flex; justify-content: space-around;'>"
        combined_chart_html += f"<div>{fig_all_time.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
        combined_chart_html += f"<div>{fig_week.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
        combined_chart_html += "</div>"

    # Get current date and time in EU format
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    update_html = f"<h4>Latest update: {current_time}</h4>"

    # Generate the complete HTML page
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Danish Data Project - POS Charts</title>
        <link rel="stylesheet" href="styles.css">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                text-align: center;
            }}
            .content-section {{
                margin: 20px auto;
                max-width: 900px;
            }}
            h3 {{
                color: #d4d4d4;
            }}
            .data-table {{
                margin: 20px auto;
                border-collapse: collapse;
                width: 100%;
                max-width: 800px;
            }}
            .data-table th, .data-table td {{
                border: 1px solid #d4d4d4;
                padding: 8px;
                text-align: left;
            }}
            .data-table th {{
                background-color: #2b2b2b;
            }}
            footer {{
                margin-top: 40px;
                color: #d4d4d4;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Danish Data Project - Frequency Analysis of POS</h1>
            {update_html}
            <p>Hey there! I'm Mikkel and this is my website which scrapes and tracks word usage in articles from DR.dk - updated twice a day. I hope you find something useful.</p>
        </header>
        <div class="content-section">
            {combined_chart_html}
        </div>
        <div class="content-section">
            {table_html}
        </div>
        <footer>
            © 2024 Mikkel Barner Johansen. All Rights Reserved.
        </footer>
    </body>
    </html>
    """

    # Define the path to index.html
    index_html_path = '/home/pi/danish_data_project/index.html'

    # Write the updated HTML content to the file
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
