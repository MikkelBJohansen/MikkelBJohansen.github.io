import sqlite3 as sq
import pandas as pd
import plotly.graph_objects as go
import subprocess
import logging
import os
import sys
from datetime import datetime, timedelta

###VERSION 1.0###

# Set up logging
log_file = '/home/pi/danish_data_project/error_log.txt'
logging.basicConfig(filename=log_file, level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

try:
    # Updated SQLite connection string to use the /home/pi/database directory
    conn = sq.connect('/home/pi/danish_data.sqlite3')

    # Query to get all-time data
    query_all_time = """
    SELECT tokens.*, articles.publication_date
    FROM tokens
    JOIN sentences ON tokens.sentence_id = sentences.sentence_id
    JOIN articles ON sentences.article_id = articles.article_id
    WHERE tokens.pos IN ('NOUN', 'VERB', 'AUX', 'ADP', 'ADV');
    """

    # Load all-time data into DataFrame
    df_all_time = pd.read_sql_query(query_all_time, conn)
    df_all_time['publication_date'] = pd.to_datetime(df_all_time['publication_date'])

    # Query to get data from the last 24 hours
    query_last_24_hours = """
    SELECT tokens.*, articles.publication_date
    FROM tokens
    JOIN sentences ON tokens.sentence_id = sentences.sentence_id
    JOIN articles ON sentences.article_id = articles.article_id
    WHERE tokens.pos IN ('NOUN', 'VERB', 'AUX', 'ADP', 'ADV')
      AND date(substr(articles.publication_date, 1, 4) || '-' || substr(articles.publication_date, 6, 2) || '-' || substr(articles.publication_date, 9, 2)) >= date('now', '-1 day');
    """

    # Load 24-hour data into DataFrame
    df_24_hours = pd.read_sql_query(query_last_24_hours, conn)
    df_24_hours['publication_date'] = pd.to_datetime(df_24_hours['publication_date'])

    # Group the data by lemma and pos for all-time data and 24-hour data
    lemma_counts_all_time = df_all_time.groupby(['lemma', 'pos']).agg(count=('lemma', 'size')).reset_index()
    lemma_counts_24_hours = df_24_hours.groupby(['lemma', 'pos']).agg(count=('lemma', 'size')).reset_index()

    # Generate top 15 occurrences data tables grouped by lemma for all-time data and 24-hour data
    pos_category_filter = ['NOUN', 'VERB', 'AUX', 'ADP', 'ADV']
    top_15_results_all_time = {}
    top_15_results_24_hours = {}

    for category in pos_category_filter:
        # All-Time Data - Explicitly sorting by count in descending order
        category_df_all_time = lemma_counts_all_time[lemma_counts_all_time['pos'] == category]
        top_15_sorted_all_time = category_df_all_time.sort_values(by='count', ascending=False).head(15)
        top_15_results_all_time[category] = top_15_sorted_all_time

        # 24-Hour Data - Explicitly sorting by count in descending order
        category_df_24_hours = lemma_counts_24_hours[lemma_counts_24_hours['pos'] == category]
        top_15_sorted_24_hours = category_df_24_hours.sort_values(by='count', ascending=False).head(15)
        top_15_results_24_hours[category] = top_15_sorted_24_hours

    # Generate HTML for Data Tables (Side-by-Side for All-Time and 24-Hour Data)
    table_html = ''
    for category in pos_category_filter:
        table_html += f"<h3>Top 15 occurrences for POS category '{category}':</h3>"
        table_html += "<div style='display: flex; justify-content: center; gap: 50px;'>"
        # All-Time Data Table
        table_html += f"<div><h4>All-Time Data</h4>{top_15_results_all_time[category].to_html(index=False, classes='data-table', border=0)}</div>"
        # 24-Hour Data Table
        table_html += f"<div><h4>Last 24 Hours Data</h4>{top_15_results_24_hours[category].to_html(index=False, classes='data-table', border=0)}</div>"
        table_html += "</div>"

    # Create figures for each POS category using the correct data from tables
    def create_chart_from_data(data_all_time, data_24_hours, title_suffix, color_scheme_all_time, color_scheme_24_hours):
        fig = go.Figure()

        # Plot All-Time Data
        for _, row in data_all_time.iterrows():
            lemma = row['lemma']
            count = row['count']
            fig.add_trace(
                go.Bar(
                    marker_color=color_scheme_all_time,
                    x=[lemma],
                    y=[count],
                    name=f'{lemma} (All Time)',
                    text=f'Word: {lemma}<br>Frequency: {count}<br>Data: All Time',
                    hoverinfo='x+y+text',
                    marker=dict(line=dict(width=1, color='black'))
                )
            )

        # Plot 24-Hour Data
        for _, row in data_24_hours.iterrows():
            lemma = row['lemma']
            count = row['count']
            fig.add_trace(
                go.Bar(
                    marker_color=color_scheme_24_hours,
                    x=[lemma],
                    y=[count],
                    name=f'{lemma} (Last 24 Hours)',
                    text=f'Word: {lemma}<br>Frequency: {count}<br>Data: Last 24 Hours',
                    hoverinfo='x+y+text',
                    marker=dict(line=dict(width=1, color='black'))
                )
            )

        fig.update_layout(
            title=f'Top 15 Most Frequent Words: {title_suffix}',
            xaxis_title='Word',
            yaxis_title='Total Number of Word Occurrences',
            barmode='group',
            plot_bgcolor='#2b2b2b',
            paper_bgcolor='#1e1e1e',
            font=dict(size=14, color='white'),
            xaxis_tickangle=-45,
            legend_title_text='Words',
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

    # Create combined charts for VERB and AUX, and individual charts for other POS categories
    combined_chart_html = ""

    # Combine VERB and AUX for charts
    combined_all_time = pd.concat([top_15_results_all_time['VERB'], top_15_results_all_time['AUX']])
    combined_24_hours = pd.concat([top_15_results_24_hours['VERB'], top_15_results_24_hours['AUX']])

    fig_combined = create_chart_from_data(
        combined_all_time,
        combined_24_hours,
        'Verbs and Auxiliaries',
        color_scheme_all_time='#82aaff',
        color_scheme_24_hours='#f07178'
    )
    combined_chart_html += "<div style='display: flex; justify-content: center; gap: 50px;'>"
    combined_chart_html += f"<div>{fig_combined.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    combined_chart_html += "</div>"

    # Create charts for NOUN, ADP, ADV categories
    for pos in ['NOUN', 'ADP', 'ADV']:
        fig = create_chart_from_data(
            top_15_results_all_time[pos],
            top_15_results_24_hours[pos],
            f'{pos.capitalize()}',
            color_scheme_all_time='#c3e88d',
            color_scheme_24_hours='#ffcb6b'
        )
        combined_chart_html += f"<h3>Charts for POS category '{pos.capitalize()}':</h3>"
        combined_chart_html += "<div style='display: flex; justify-content: center; gap: 50px;'>"
        combined_chart_html += f"<div>{fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
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
        <title>Danish Data Project - Word Frequency Charts</title>
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
                max-width: 1200px;
            }}
            h3 {{
                color: #d4d4d4;
            }}
            .data-table {{
                margin: 20px auto;
                border-collapse: collapse;
                width: 100%;
                max-width: 500px;
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
            <h1>Danish Data Project - Word Frequency Charts</h1>
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
