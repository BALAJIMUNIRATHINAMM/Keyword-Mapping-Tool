import streamlit as st
import pandas as pd
from flashtext import KeywordProcessor
from io import BytesIO
from stqdm import stqdm
from datetime import datetime
import os
print(os.listdir("/"))


# Enable progress bar for pandas
stqdm.pandas()

# Set Streamlit Page Config
st.set_page_config(
    page_title="Keyword Mapping Tool",
    page_icon="📌",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'About': "Keyword Mapping Tool for conditional and non-conditional keyword mapping."}
)

st.markdown("<h1 style='text-align: center; color: #007BFF;'>🍳 Keyword Mapping Tool</h1>", unsafe_allow_html=True)
st.info("Supports both conditional and non-conditional keyword mapping. Allows manual keyword file uploads for mapping.")

@st.cache_data(ttl=1200)
def load_data(file):
    try:
        if file.name.endswith(".csv"):
            return pd.read_csv(file).fillna("-")
        elif file.name.endswith(".xlsx"):
            return pd.read_excel(file).fillna("-")
        elif file.name.endswith(".json"):
            return pd.read_json(file).fillna("-")
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return None

def concatenate_columns(df, columns):
    return df[columns].apply(lambda row: " ".join(row.dropna().astype(str)), axis=1).fillna("-")

def download_dataframe(df, file_format):
    output = BytesIO()
    if file_format == "csv":
        df.to_csv(output, index=False)
    elif file_format == "xlsx":
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
    elif file_format == "json":
        df.to_json(output, orient="records", indent=4)
    output.seek(0)
    return output

st.header("📂 Upload Datasets")

col1, col2= st.columns(2)
with col1:
    desc_dataset_file = st.file_uploader("📄 Upload Description File (CSV, Excel, JSON)", type=["csv", "xlsx", "json"], key="desc_file")
    desc_columns = []
    if desc_dataset_file:
        desc_dataset = load_data(desc_dataset_file)
        st.dataframe(desc_dataset.head(1000), use_container_width=True)
        st.warning('Preview limited to the first 1000 rows.', icon="⚠️")
        if desc_dataset is not None:
            desc_columns = st.multiselect('📌 Select Description Columns', options=desc_dataset.columns)
            if desc_columns:
                desc_dataset['Concatenated_Description'] = concatenate_columns(desc_dataset, desc_columns)

with col2:
    key_dataset_file = st.file_uploader("🔑 Upload Keyword & Product File (CSV, Excel, JSON)", type=["csv", "xlsx", "json"], key="keyword_file")
    st.warning('Preview limited to the first 1000 rows.', icon="⚠️")
        

manual_keywords = st.text_area("✍️ Or enter keywords manually (comma-separated)", "")

key_columns, prod_columns = [], []
key_data = None

if key_dataset_file:
    key_data = load_data(key_dataset_file)
    if key_data is not None:
        col11, col22 = st.columns(2)
        with col22:
            key_columns = st.multiselect('🔍 Select Keyword Columns', options=key_data.columns)
        with col11:
            prod_columns = st.multiselect('📦 Select Product Columns', options=key_data.columns)
elif manual_keywords:
    key_data = pd.DataFrame({"Keywords": [kw.strip() for kw in manual_keywords.split(",") if kw.strip()]})
    key_columns = ["Keywords"]

if not key_columns:
    st.warning("⚠️ Please provide at least one keyword column.")

if desc_columns and key_data is not None and key_columns:
    if st.button("🚀 Start Mapping", key="start_mapping"):
        st.info("🔄 Initializing Keyword & Product Mapping...")
        
        keyword_processor = KeywordProcessor()
        product_map = {}
        
        for _, row in key_data.iterrows():
            keywords = [row[col] for col in key_columns if pd.notnull(row[col])]
            products = [row[col] for col in prod_columns if pd.notnull(row[col])]
            for keyword in keywords:
                keyword_processor.add_keyword(keyword)
                product_map[keyword] = ", ".join(products) if products else "-"
        
        if 'Concatenated_Description' in desc_dataset:
            st.info("🔎 Processing Descriptions...")
            
            def extract_keywords(description):
                matched_keywords = list(set(keyword_processor.extract_keywords(description)))
                return ", ".join(matched_keywords) if matched_keywords else "-"
            
            desc_dataset['Mapped_Keyword'] = desc_dataset['Concatenated_Description'].progress_apply(extract_keywords)
            
            desc_dataset['Mapped_Product'] = desc_dataset['Mapped_Keyword'].apply(
                lambda x: ", ".join(set(product_map.get(k, "-") for k in x.split(", ") if k)) if x != "-" else "-"
            )
            
            st.success("✅ Mapping Completed!")
            st.dataframe(desc_dataset.head(), use_container_width=True)
            
            date_str = datetime.today().strftime("%Y_%m_%d_%H_%M")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button("⬇️ Download Excel", data=download_dataframe(desc_dataset, "xlsx"), file_name=f"keyword_mapping_{date_str}.xlsx")
            with col2:
                st.download_button("⬇️ Download CSV", data=download_dataframe(desc_dataset, "csv"), file_name=f"keyword_mapping_{date_str}.csv")
            with col3:
                st.download_button("⬇️ Download JSON", data=download_dataframe(desc_dataset, "json"), file_name=f"keyword_mapping_{date_str}.json")


st.markdown(
    """
    <style>
    .footer {position: fixed; left: 0; bottom: -17px; width: 100%; background-color: #b1b1b5; color: black; text-align: center;}
    </style>
    <div class="footer"><p>© 2025 Draup Dataflow Engine</p></div>
    """, unsafe_allow_html=True
)
