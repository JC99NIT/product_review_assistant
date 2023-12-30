import os
import json
import shutil
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv
from enum import Enum
import time
import importlib
import os

# Load environment variables
load_dotenv()

api_host = os.environ.get("HOST", "0.0.0.0")
api_port = int(os.environ.get("PORT", 8080))

# Paths for data files
csv_path = "../examples/data/csv_reviews.jsonl"

with st.sidebar:
    st.markdown(
    """
    ### About
    This app is an LLM-Powered Product Review Research Assistant
    """)

# Enum for data sources
class DataSource(Enum):
    CSV = 'CSV'

# Streamlit UI elements
st.title("Product Review Research with LLM App")
data_sources = st.multiselect(
    'Choose data sources',
    [source.value for source in DataSource]
)

uploaded_file = st.file_uploader(
    "Upload a CSV file",
    type=("csv"),
    disabled=(DataSource.CSV.value not in data_sources)
)

# Handle CSV upload
if uploaded_file and DataSource.CSV.value in data_sources:
    df = pd.read_csv(uploaded_file)

    # Start progress bar
    progress_bar = st.progress(0, "Processing your file. Please wait.")
    total_rows = len(df)

    # Format the DataFrame rows and write to a jsonlines file
    formatted_rows = []

    for _, row in df.iterrows():
        # Format each row and append to the list
        formatted_rows.append(
            {"doc": ', '.join([f"{title}: {value}" for title, value in row.items()])}
        )

    # Write the formatted rows to the jsonlines file
    with open(csv_path, 'w') as outfile:
        for obj in formatted_rows:
            # Update the progress bar
            time.sleep(0.1)
            current_progress = (len(formatted_rows) / total_rows)
            progress_bar.progress(current_progress)
            outfile.write(json.dumps(obj) + '\n')

    # Finish progress bar when done
    progress_bar.progress(1.0, "Your file is uploaded successfully")

reviews = []
with open(csv_path, 'r') as file:
    for line in file:
        reviews.append(json.loads(line))
        
column_names = ['category', 'subcategory', 'retailer', 'brand', 'product_title', 'review_text']

parsed_data = [
    {col: kv.split(': ')[1] for kv in d['doc'].split(', ') if (col := kv.split(': ')[0]) in column_names}
    for d in reviews
]

all_reviews = pd.DataFrame(parsed_data)
products = all_reviews['product_title'].unique()

'Please select two products and ask a question relevant to the selected products.'

product_1 = st.selectbox('Product 1', products, 0)
selected_products = [product_1]
product_2 = st.selectbox('Product 2', products, 1)
selected_products += [product_2]

question_placeholder = "Determine 3 specific differences that make one product better than the other. Don't mention products similarities."

user_input = st.text_input(
    "Search for something for selected products",
    placeholder=f"{question_placeholder} Products are: {', '.join(selected_products)}",
    disabled=not data_sources)

# Handle data sources
if DataSource.CSV.value not in data_sources and os.path.exists(csv_path):
    os.remove(csv_path)

if user_input:
    question = f"{user_input} Product 1: {selected_products[0]} & Product 2: {selected_products[1]}"
    st.write("Current Question:", question)

    # Handle Pathway API request if data source is selected and a question is provided
    if data_sources and question:
        if not os.path.exists(csv_path):
            st.error("Failed to process reviews file")

        url = f'http://{api_host}:{api_port}/'
        data = {"query": question}

        response = requests.post(url, json=data)

        if response.status_code == 200:
            st.write("### Answer")
            st.write(response.json())
        else:
            st.error(f"Failed to send data to Pathway API. Status code: {response.status_code}")
