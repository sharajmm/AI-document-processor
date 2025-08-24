import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

# Import our custom modules
from config import Config
from ocr_utils import get_ocr_processor
from ai_utils import get_ai_processor
from db_utils import get_db_manager
from github_utils import get_github_storage

# Page configuration
st.set_page_config(
    page_title="AI Document Processor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern dark theme CSS
st.markdown('''
<style>
body, .main, .block-container {
    background: linear-gradient(135deg, #18181b 0%, #23272f 100%);
    color: #e5e7eb;
}
.main-header {
    font-size: 3rem;
    font-weight: 700;
    color: #7c3aed;
    text-align: center;
    margin-bottom: 2rem;
    letter-spacing: 2px;
    text-shadow: 0 2px 8px #23272f;
}
.section-header {
    font-size: 1.7rem;
    color: #3b82f6;
    margin-top: 2rem;
    margin-bottom: 1rem;
    font-weight: 600;
    letter-spacing: 1px;
}
.document-card {
    border: 1px solid #23272f;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    background: linear-gradient(120deg, #23272f 60%, #18181b 100%);
    box-shadow: 0 4px 24px rgba(60, 60, 120, 0.18);
}
.success-message {
    color: #22c55e;
    font-weight: bold;
}
.error-message {
    color: #eab308;
    font-weight: bold;
}
.stTabs [role="tab"] {
    background: #23272f;
    color: #e5e7eb;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    margin-right: 2px;
    border: 1px solid #23272f;
}
.stTabs [role="tab"][aria-selected="true"] {
    background: linear-gradient(90deg, #7c3aed 0%, #3b82f6 100%);
    color: #fff;
    border-bottom: 2px solid #22c55e;
}
.stButton>button {
    background: linear-gradient(90deg, #3b82f6 0%, #7c3aed 100%);
    color: #fff;
    border-radius: 8px;
    font-weight: 600;
    border: none;
    box-shadow: 0 2px 8px #23272f;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #22c55e 0%, #eab308 100%);
    color: #fff;
}
.stTextInput>div>input {
    border-radius: 8px;
    border: 1px solid #23272f;
    padding: 0.5rem;
    background: #18181b;
    color: #e5e7eb;
}
.stTextArea>div>textarea {
    border-radius: 8px;
    border: 1px solid #23272f;
    padding: 0.5rem;
    background: #18181b;
    color: #e5e7eb;
}
.stDownloadButton>button {
    background: linear-gradient(90deg, #eab308 0%, #22c55e 100%);
    color: #fff;
    border-radius: 8px;
    font-weight: 600;
    border: none;
}
.stDownloadButton>button:hover {
    background: linear-gradient(90deg, #3b82f6 0%, #7c3aed 100%);
    color: #fff;
}
</style>
''', unsafe_allow_html=True)

def check_configuration():
    """Check if the application is properly configured"""
    try:
        Config.validate_config()
        return True, ""
    except ValueError as e:
        return False, str(e)

def initialize_services():
    """Initialize all services and check their status"""
    if 'services_initialized' not in st.session_state:
        try:
            st.session_state.ocr_processor = get_ocr_processor()
            st.session_state.ai_processor = get_ai_processor()
            st.session_state.db_manager = get_db_manager()
            st.session_state.github_storage = get_github_storage()
            st.session_state.services_initialized = True
        except Exception as e:
            st.error(f"Error initializing services: {str(e)}")
            st.session_state.services_initialized = False

def display_header():
    """Display the main application header"""
    st.markdown('<h1 class="main-header">AI Document Processor</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Configuration status
    config_valid, config_error = check_configuration()
    if not config_valid:
        st.error(f"Configuration Error: {config_error}")
        st.info("Please check your .env file and ensure all required values are set.")
        return False
    return True

def upload_section():
    st.markdown('<h2 class="section-header">Upload Documents</h2>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Choose documents to process",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Supported formats: PDF, JPG, PNG"
    )
    tags_input = st.text_input("Tags (comma separated)", "", help="Add tags to describe your document (e.g. invoice, personal, 2025)")
    if uploaded_files:
        process_col, status_col = st.columns([1, 1])
        with process_col:
            if st.button("Process Documents", type="primary"):
                process_uploaded_files(uploaded_files, status_col, tags_input)

def process_uploaded_files(uploaded_files: List[Any], status_col, tags_input):
    with status_col:
        status_container = st.container()
    progress_bar = st.progress(0)
    total_files = len(uploaded_files)
    results = []
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            with status_container:
                st.info(f"Processing {uploaded_file.name}...")
            progress = (idx + 1) / total_files
            progress_bar.progress(progress)
            file_size = len(uploaded_file.getvalue())
            max_size = Config.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size:
                st.warning(f"Skipping {uploaded_file.name}: File too large ({file_size / 1024 / 1024:.1f}MB)")
                continue
            uploaded_file.seek(0)
            extracted_text = st.session_state.ocr_processor.process_document(uploaded_file)
            if not extracted_text.strip():
                st.warning(f"No text extracted from {uploaded_file.name}")
                continue
            ai_results = st.session_state.ai_processor.process_document_text(extracted_text)
            uploaded_file.seek(0)
            file_content = uploaded_file.getvalue()
            github_url = st.session_state.github_storage.upload_file(
                file_content, uploaded_file.name
            )
            if not github_url:
                st.warning(f"Failed to upload {uploaded_file.name} to GitHub storage")
                github_url = "Upload failed"
            # Clean up tags: remove extra spaces, store as comma-separated
            cleaned_tags = ','.join([t.strip() for t in tags_input.split(',') if t.strip()])
            document = st.session_state.db_manager.create_document(
                filename=uploaded_file.name,
                original_filename=uploaded_file.name,
                file_type=uploaded_file.name.split('.')[-1].lower(),
                file_size=file_size,
                extracted_text=extracted_text,
                ai_results=ai_results,
                github_url=github_url,
                tags=cleaned_tags
            )
            st.session_state.db_manager.log_action(document.id, "upload", "user", f"Uploaded {uploaded_file.name}")
            results.append({
                'filename': uploaded_file.name,
                'status': 'success',
                'document_type': ai_results.get('document_type', 'unknown'),
                'confidence': ai_results.get('confidence_score', 0),
                'summary': ai_results.get('summary', ''),
                'tags': tags_input
            })
            with status_container:
                st.success(f"Successfully processed {uploaded_file.name}")
        except Exception as e:
            results.append({
                'filename': uploaded_file.name,
                'status': 'error',
                'error': str(e)
            })
            with status_container:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    if results:
        st.markdown("### Processing Results")
        success_count = len([r for r in results if r['status'] == 'success'])
        st.info(f"Successfully processed {success_count}/{len(results)} documents")
        for result in results:
            if result['status'] == 'success':
                st.success(f"{result['filename']} → {result['document_type']} (confidence: {result['confidence']:.2f}) | Tags: {result['tags']}")
            else:
                st.error(f"{result['filename']} → {result['error']}")

def search_and_display_section():
    """Handle document search and display"""
    st.markdown('<h2 class="section-header">Search & Browse Documents</h2>', unsafe_allow_html=True)
    
    # Search controls
    search_col1, search_col2, search_col3 = st.columns([2, 1, 1])

    with search_col1:
        search_query = st.text_input("Search documents", placeholder="Enter keywords...")

    with search_col2:
        document_types = ['all'] + st.session_state.db_manager.get_document_types()
        selected_type = st.selectbox("Document Type", document_types)

    with search_col3:
        date_range = st.date_input(
            "Date Range",
            value=None,
            help="Filter by upload date"
        )

    st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)
    tag_query = st.text_input("Tag Based Search Files", placeholder="Enter tag(s) to search...", key="tag_search_bar", help="Search files by tags. Use comma to separate multiple tags.",
                             label_visibility="visible")
    st.markdown('<style>#tag_search_bar {font-size:1.3rem !important; height:3rem !important;}</style>', unsafe_allow_html=True)

    # Search button
    if st.button("Search Documents") or search_query or selected_type != 'all' or tag_query:
        display_documents(search_query, selected_type, date_range, tag_query)

def display_documents(search_query: str = None, document_type: str = None, date_range=None, tag_query: str = None):
    """Display filtered documents"""
    try:
        date_from = None
        date_to = None

        if date_range:
            if isinstance(date_range, list) and len(date_range) == 2:
                date_from = datetime.combine(date_range[0], datetime.min.time())
                date_to = datetime.combine(date_range[1], datetime.max.time())
            elif not isinstance(date_range, list):
                date_from = datetime.combine(date_range, datetime.min.time())
                date_to = datetime.combine(date_range, datetime.max.time())

        # Multi-tag OR search: split tag_query by comma, trim spaces
        tags_list = [t.strip() for t in tag_query.split(',') if t.strip()] if tag_query else []
        all_documents = st.session_state.db_manager.search_documents(
            search_query=search_query,
            document_type=document_type if document_type != 'all' else None,
            date_from=date_from,
            date_to=date_to,
            limit=500
        )
        if tags_list:
            documents = [
                doc for doc in all_documents if doc.tags and any(
                    tag.lower() == t.strip().lower()
                    for tag in tags_list
                    for t in doc.tags.split(',')
                )
            ]
        else:
            documents = all_documents[:50]

        if not documents:
            st.info("No documents found matching your criteria.")
            return

        st.write(f"Found {len(documents)} document(s)")

        for doc in documents:
            with st.expander(f"📄 {doc.original_filename} ({doc.document_type})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write("**Summary:**")
                    st.write(doc.summary or "No summary available")

                    fields = doc.extracted_fields if isinstance(doc.extracted_fields, dict) else {}
                    if fields:
                        st.write("**Extracted Fields:**")
                        if fields.get('names'):
                            st.write(f"Names: {', '.join(fields['names'])}")
                        if fields.get('dates'):
                            st.write(f"Dates: {', '.join(fields['dates'])}")
                        if fields.get('amounts'):
                            st.write(f"Amounts: {', '.join(fields['amounts'])}")

                with col2:
                    st.write("**Details:**")
                    st.write(f"Type: {doc.document_type}")
                    st.write(f"Confidence: {doc.confidence_score:.2f}")
                    st.write(f"Upload Date: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"File Size: {doc.file_size / 1024:.1f} KB")
                    st.write(f"Tags: {doc.tags}")
                    # Transparent audit log display (read-only, minimal info)
                    st.markdown("#### Audit Trail")
                    logs = st.session_state.db_manager.get_audit_logs(doc.id)
                    for log in logs:
                        st.markdown(f"<div style='border-left:4px solid #7c3aed;padding-left:1rem;margin-bottom:1rem;opacity:0.7;'>"
                                    f"<span style='color:#eab308;'>Block: {log.id}</span> "
                                    f"<span style='color:#3b82f6;'>{log.timestamp.strftime('%Y-%m-%d %H:%M')}</span> "
                                    f"<span style='color:#e5e7eb;'>Hash: {abs(hash(str(log.id)+str(log.timestamp)))} </span>"
                                    "</div>", unsafe_allow_html=True)

                    if doc.github_url and doc.github_url != "Upload failed":
                        st.link_button("📥 Download Original", doc.github_url)

                # Show extracted text in collapsible section
                if doc.extracted_text:
                    with st.expander("View Extracted Text"):
                        st.text_area("Full Text", doc.extracted_text, height=200, disabled=True, key=f"text_{doc.id}")

    except Exception as e:
        st.error(f"Error retrieving documents: {str(e)}")

def export_section():
    """Handle data export functionality"""
    st.markdown('<h2 class="section-header">Export Data</h2>', unsafe_allow_html=True)
    
    export_format = st.selectbox("Export Format", ["CSV", "Excel"])
    include_text = st.checkbox("Include extracted text", value=False)
    st.write("")
    if st.button("Export All Documents", type="secondary"):
        export_documents(export_format, include_text)

def export_documents(format_type: str, include_text: bool):
    """Export documents to CSV or Excel"""
    try:
        documents = st.session_state.db_manager.get_all_documents(limit=1000)
        
        if not documents:
            st.warning("No documents to export")
            return
        
        # Prepare data
        export_data = []
        for doc in documents:
            row = {
                'ID': doc.id,
                'Filename': doc.original_filename,
                'Document Type': doc.document_type,
                'Confidence Score': doc.confidence_score,
                'Summary': doc.summary,
                'Upload Date': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'File Size (KB)': doc.file_size / 1024 if doc.file_size else 0,
                'GitHub URL': doc.github_url
            }
            
            # Add extracted fields
            fields = doc.extracted_fields if isinstance(doc.extracted_fields, dict) else {}
            if fields:
                row.update({
                    'Names': ', '.join(fields.get('names', [])),
                    'Dates': ', '.join(fields.get('dates', [])),
                    'Amounts': ', '.join(fields.get('amounts', [])),
                    'Addresses': ', '.join(fields.get('addresses', [])),
                    'Phone Numbers': ', '.join(fields.get('phone_numbers', [])),
                    'Emails': ', '.join(fields.get('email_addresses', []))
                })
            
            if include_text:
                row['Extracted Text'] = doc.extracted_text
            
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        
        # Generate file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "CSV":
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"documents_export_{timestamp}.csv",
                mime="text/csv"
            )
        else:  # Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Documents')
            
            st.download_button(
                label="📥 Download Excel",
                data=buffer.getvalue(),
                file_name=f"documents_export_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.success(f"Prepared export of {len(documents)} documents")
    
    except Exception as e:
        st.error(f"Error exporting documents: {str(e)}")

def statistics_section():
    """Display application statistics"""
    st.markdown('<h2 class="section-header">Statistics</h2>', unsafe_allow_html=True)
    
    try:
        stats = st.session_state.db_manager.get_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Total Documents",
                value=stats['total_documents']
            )
        
        with col2:
            st.metric(
                label="Recent Uploads",
                value=stats['recent_uploads'],
                help="Uploads in the last 7 days"
            )
        
        with col3:
            if stats['document_types']:
                most_common_type = max(stats['document_types'].items(), key=lambda x: x[1])
                st.metric(
                    label="Most Common Type",
                    value=most_common_type[0].title(),
                    delta=f"{most_common_type[1]} docs"
                )
        
        # File types percentage breakdown
        db = st.session_state.db_manager
        all_docs = db.get_all_documents(limit=1000)
        file_type_counts = {}
        for doc in all_docs:
            ext = doc.file_type.lower()
            # Group common types
            if ext in ['pdf']:
                key = 'PDF'
            elif ext in ['doc', 'docx', 'word']:
                key = 'Word'
            elif ext in ['jpg', 'jpeg', 'png']:
                key = 'Image'
            else:
                key = ext.upper()
            file_type_counts[key] = file_type_counts.get(key, 0) + 1
        if file_type_counts:
            st.markdown("### File Types Percentage Breakdown")
            type_df = pd.DataFrame(
                list(file_type_counts.items()),
                columns=['File Type', 'Count']
            )
            import plotly.express as px
            fig = px.pie(type_df, names='File Type', values='Count', title='File Types Distribution (%)', color_discrete_sequence=px.colors.sequential.RdBu, hole=0.3)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

def sidebar():
    """Create the sidebar with navigation and controls"""
    with st.sidebar:
        st.markdown("<div style='font-size:2rem;font-weight:700;color:#eab308;margin-bottom:1rem;'>AI Document Processor</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #3b82f6;margin:1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:1.2rem;font-weight:600;color:#eab308;margin-bottom:1.2rem;'>Tips & How to Use</div>", unsafe_allow_html=True)
        st.markdown("<div style='display:flex;flex-direction:column;gap:1.5rem;'>"
                    "<div style='background:#23272f;border-radius:16px;padding:1.2rem 2rem;font-size:1.15rem;color:#e5e7eb;'>Upload your PDF or image documents using the Upload tab. Supported formats: PDF, JPG, PNG.</div>"
                    "<div style='background:#23272f;border-radius:16px;padding:1.2rem 2rem;font-size:1.15rem;color:#e5e7eb;'>After upload, click 'Process Documents' to extract and analyze content automatically.</div>"
                    "<div style='background:#23272f;border-radius:16px;padding:1.2rem 2rem;font-size:1.15rem;color:#e5e7eb;'>Use the Search tab to find documents by keywords, type, or date range.</div>"
                    "<div style='background:#23272f;border-radius:16px;padding:1.2rem 2rem;font-size:1.15rem;color:#e5e7eb;'>Export processed data to CSV or Excel in the Export tab.</div>"
                    "<div style='background:#23272f;border-radius:16px;padding:1.2rem 2rem;font-size:1.15rem;color:#e5e7eb;'>Check document statistics and trends in the Statistics tab.</div>"
                    "</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid #3b82f6;margin:2rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:1.1rem;font-weight:500;color:#e5e7eb;margin-bottom:1rem;'>About</div>", unsafe_allow_html=True)
        st.write("AI-powered document processing, search, and export.")

def main():
    """Main application function"""
    # Initialize services
    initialize_services()
    
    if not st.session_state.get('services_initialized', False):
        st.error("Failed to initialize application services. Please check your configuration.")
        return
    
    # Display header and check configuration
    config_valid = display_header()
    
    if not config_valid:
        st.stop()
    
    # Create sidebar
    sidebar()
    
    # Main content tabs
    tab_styles = """
    <style>
    .stTabs [role="tab"] {
        min-width: 180px;
        height: 56px;
        font-size: 1.2rem;
        margin-right: 24px !important;
        padding: 0 32px;
        border-radius: 16px 16px 0 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """
    st.markdown(tab_styles, unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload", "Search", "Export", "Statistics", "Audit Trail"])
    
    with tab1:
        upload_section()
    with tab2:
        search_and_display_section()
    with tab3:
        export_section()
    with tab4:
        statistics_section()
    with tab5:
        audit_trail_section()

def audit_trail_section():
    st.markdown('<h2 class="section-header">Audit Trail</h2>', unsafe_allow_html=True)
    st.write("This is a transparent, read-only blockchain-style audit log of all document actions.")
    db = st.session_state.db_manager
    logs = db.get_audit_logs_for_all()
    for log in logs:
        doc = db.get_document_by_id(log.document_id)
        doc_name = doc.original_filename if doc else "Unknown Document"
        st.markdown(f"<div style='border-left:4px solid #7c3aed;padding-left:1rem;margin-bottom:1rem;opacity:0.7;'>"
                    f"<span style='color:#eab308;'>Block: {log.id}</span> "
                    f"<span style='color:#3b82f6;'>{log.timestamp.strftime('%Y-%m-%d %H:%M')}</span> "
                    f"<span style='color:#eab308;'>Document: {doc_name}</span> "
                    f"<span style='color:#e5e7eb;'>Hash: {abs(hash(str(log.id)+str(log.timestamp)))} </span>"
                    "</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
