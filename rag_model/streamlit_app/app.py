import os
import streamlit as st
from haystack.document_stores import OpenSearchDocumentStore
from haystack.nodes import FARMReader, DenseRetriever
from haystack.pipelines import ExtractiveQAPipeline
from transformers import pipeline

# Configurations
opensearch_url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")

# Initialize OpenSearch document store
document_store = OpenSearchDocumentStore(
    host="opensearch",
    port=9200,
    username="",
    password="",
    index="document"
)

# Initialize retriever and reader
retriever = DenseRetriever(document_store=document_store, embedding_model="sentence-transformers/all-MiniLM-L6-v2")
reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2")

# Pipeline setup
pipe = ExtractiveQAPipeline(reader, retriever)

# Streamlit UI
st.title("LLM RAG Model with OpenSearch")
st.write("Ask questions and get answers from the knowledge base powered by OpenSearch and an open-source LLM.")

query = st.text_input("Enter your question:")
if query:
    prediction = pipe.run(query=query, params={"Retriever": {"top_k": 10}, "Reader": {"top_k": 3}})
    st.write("Answers:")
    for answer in prediction["answers"]:
        st.write(answer.answer)