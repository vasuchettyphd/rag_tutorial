# app.py

import os
import time
import streamlit as st
from typing import Optional, List
from haystack.schema import Document
from haystack.pipelines import ExtractiveQAPipeline
from haystack.nodes import BM25Retriever, FARMReader
from haystack.document_stores import OpenSearchDocumentStore

# Environment variables for OpenSearch host and port
host = os.getenv("OPENSEARCH_HOST", "opensearch")
port = int(os.getenv("OPENSEARCH_PORT", "9200"))

def create_document_store() -> Optional[OpenSearchDocumentStore]:
    """
    Creates and initializes the OpenSearch document store with a retry mechanism.
    The retry mechanism helps handle cases where OpenSearch might not be
    immediately available when the application starts.
    """
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            # Initialize OpenSearchDocumentStore without setting similarity
            document_store = OpenSearchDocumentStore(
                host=host,
                port=port,
                scheme="http",
                index="document",
                verify_certs=False,
                timeout=300
            )
            # Test the connection by fetching document count
            document_store.get_document_count()
            st.success("✅ Successfully connected to OpenSearch")
            return document_store

        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⚠️ Attempt {attempt + 1}/{max_retries}: Failed to connect to OpenSearch. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                st.error(f"❌ Failed to connect to OpenSearch after {max_retries} attempts: {str(e)}")
                st.info("ℹ️ Please ensure OpenSearch is running and accessible")
                return None

def create_retriever(document_store: OpenSearchDocumentStore) -> BM25Retriever:
    """
    Creates a BM25Retriever instance for efficient and memory-friendly retrieval.
    """
    return BM25Retriever(document_store=document_store)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 10) -> List[str]:
    """
    Splits text into overlapping chunks of approximately equal size.
    This helps maintain context across chunk boundaries.

    Args:
        text: The input text to be chunked
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Adjust chunk end to not split words
        if end < text_length:
            # Find the last period or space before the chunk_size
            last_period = text.rfind('.', start, end)
            last_space = text.rfind(' ', start, end)
            end = max(last_period, last_space)
            if end <= start:  # If no suitable breaking point found
                end = text.find(' ', start + chunk_size)
                if end == -1:  # If no space found
                    end = text_length
        else:
            end = text_length

        # Add the chunk
        chunks.append(text[start:end].strip())

        # Move start position for next chunk, accounting for overlap
        start = end - overlap

    return chunks

def process_and_index_documents(
    document_store: OpenSearchDocumentStore,
    retriever: BM25Retriever,
    content: str
) -> int:
    """
    Processes text content into documents with intelligent chunking
    and indexes them in OpenSearch using BM25.

    Returns the number of chunks processed.
    """
    # Create chunks with overlap to maintain context
    chunks = chunk_text(content)

    # Convert chunks to Documents
    documents = [
        Document(content=chunk)
        for chunk in chunks
        if chunk.strip()
    ]

    if not documents:
        raise ValueError("🚫 No valid documents created from input text")

    # Index documents in batches
    batch_size = 8
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        document_store.write_documents(batch)

    # No need to update embeddings since BM25 does not use embeddings

    return len(documents)

def main():
    st.title("🔍 Semantic Search RAG System")
    st.write("A powerful question-answering system using BM25 retrieval and neural search.")

    # Initialize components with progress indicators
    with st.spinner("🛠️ Initializing document store..."):
        document_store = create_document_store()
        if not document_store:
            st.stop()

    with st.spinner("🔍 Initializing retriever..."):
        retriever = create_retriever(document_store)

    with st.spinner("⚙️ Setting up QA pipeline..."):
        reader = FARMReader(
            model_name_or_path="deepset/roberta-base-squad2",
            use_gpu=True,
            context_window_size=500,
            return_no_answer=True
        )
        pipeline = ExtractiveQAPipeline(reader=reader, retriever=retriever)

    # Display system status
    total_docs = document_store.get_document_count()
    st.sidebar.metric("📚 Documents in Database", total_docs)

    # Document upload section
    st.header("📚 Document Management")
    uploaded_file = st.file_uploader(
        "Upload a text file to add to your knowledge base",
        type=['txt'],
        help="Upload text files to build your knowledge base. The system will process them for semantic search."
    )

    if uploaded_file:
        try:
            with st.spinner("📄 Processing document and indexing..."):
                content = uploaded_file.read().decode('utf-8')
                num_docs = process_and_index_documents(document_store, retriever, content)
                st.success(f"✅ Successfully processed and indexed {num_docs} document chunks")

                # Update document count
                new_total = document_store.get_document_count()
                st.sidebar.metric("📚 Documents in Database", new_total, delta=new_total - total_docs)

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("ℹ️ Try uploading a different file or check the file format")

    # Question answering section
    st.header("❓ Ask Questions")
    query = st.text_input(
        "What would you like to know?",
        help="Ask questions in natural language - the system understands context and meaning"
    )

    if query:
        try:
            with st.spinner("🔍 Searching for answers..."):
                results = pipeline.run(
                    query=query,
                    params={
                        "Retriever": {"top_k": 5},  # BM25 typically benefits from more retrieved documents
                        "Reader": {"top_k": 3}
                    }
                )

                if results["answers"]:
                    st.subheader("📝 Answers")
                    for idx, answer in enumerate(results["answers"], 1):
                        confidence = round(answer.score * 100, 2)

                        # Create an expandable section for each answer
                        with st.expander(f"Answer {idx} (Confidence: {confidence}%)"):
                            st.markdown(f"> **Answer:** {answer.answer}")
                            st.markdown("**Context:**")
                            st.markdown(f"```\n{answer.context}\n```")
                else:
                    st.info("ℹ️ No answers found. Try rephrasing your question or adding more documents to the knowledge base.")

        except Exception as e:
            st.error(f"❌ Error processing question: {str(e)}")
            st.info("ℹ️ Try rephrasing your question or check if OpenSearch is accessible")

if __name__ == "__main__":
    main()