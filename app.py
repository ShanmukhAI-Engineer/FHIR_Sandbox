"""
SynthFHIR - Streamlit UI
Synthetic FHIR Data Generator with RAG
"""

import os
import json
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page config first
st.set_page_config(
    page_title="SynthFHIR - Synthetic Data Generator",
    page_icon="🏥",
    layout="wide"
)

# Import modules
from config import (
    get_enabled_resources,
    get_resource_config,
    get_resource_display_names,
    QUICK_INPUT_OPTIONS,
    LLM_SETTINGS,
    OUTPUT_DIR,
)
from generator.llm import get_llm, get_active_llm_name
from generator.table_generator import TableGenerator
from rag import get_retriever, get_vector_store
from utils import CSVExporter, MD5Hasher, validate_data
from utils.dependency_graph import DependencyGraph
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger()
logger.info("Starting SynthFHIR UI")


def init_session_state():
    """Initialize session state variables"""
    if "generated_data" not in st.session_state:
        st.session_state.generated_data = None
    if "generation_status" not in st.session_state:
        st.session_state.generation_status = None
    if "indexed_resources" not in st.session_state:
        st.session_state.indexed_resources = set()
    if "session_history" not in st.session_state:
        st.session_state.session_history = {} # resource -> List[Dict]


def render_sidebar():
    """Render sidebar with settings and info"""
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # LLM Info
        st.subheader("LLM Configuration")
        llm_name = get_active_llm_name()
        st.info(f"Active LLM: **{llm_name.upper()}**")
        
        # Check Enterprise LLM configuration
        base_url = os.getenv("ENTERPRISE_BASE_URL")
        client_id = os.getenv("ENTERPRISE_CLIENT_ID")
        client_secret = os.getenv("ENTERPRISE_CLIENT_SECRET")
        if base_url and client_id and client_secret:
            st.success("✅ Enterprise LLM configured (OAuth2)")
            st.caption(f"Base URL: {base_url[:40]}..." if len(base_url) > 40 else f"Base URL: {base_url}")
        else:
            st.error("❌ Enterprise OAuth2 configuration incomplete")
            if not base_url: st.warning("ENTERPRISE_BASE_URL missing")
            if not client_id: st.warning("ENTERPRISE_CLIENT_ID missing")
            if not client_secret: st.warning("ENTERPRISE_CLIENT_SECRET missing")
        
        st.divider()
        
        # RAG Status
        st.subheader("Knowledge Base")
        try:
            vector_store = get_vector_store()
            doc_count = vector_store.count()
            st.metric("Documents Indexed", doc_count)
            
            if st.button("🔄 Reindex Documents"):
                with st.spinner("Indexing..."):
                    index_all_resources()
                    st.success("Indexing complete!")
                    st.rerun()
        except Exception as e:
            st.error(f"Vector store error: {e}")
        
        st.divider()
        
        # About
        st.subheader("About")
        st.markdown("""
        **SynthFHIR** generates synthetic healthcare data matching your Snowflake DDL structure.
        
        - 🏥 FHIR R4 compatible
        - 🔒 MD5 hashing for PHI
        - 📊 CSV export
        - 🤖 RAG-enhanced generation
        """)


def render_main_ui():
    """Render main UI"""
    st.title("🏥 SynthFHIR")
    st.subheader("Synthetic FHIR Data Generator")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📝 Generate", "📚 Knowledge Base", "📊 Results"])
    
    with tab1:
        render_generation_tab()
    
    with tab2:
        render_knowledge_tab()
    
    with tab3:
        render_results_tab()


def render_generation_tab():
    """Render the generation tab"""
    
    # Prompt input
    st.markdown("### 💬 Prompt")
    user_prompt = st.text_area(
        "Describe what data you want to generate:",
        placeholder="Generate 5 diabetic patients in Texas with linked coverage and claims...",
        height=100,
        key="user_prompt"
    )
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Resources")
        enabled_resources = get_enabled_resources()
        resource_display_map = get_resource_display_names()
        selected_display_names = st.multiselect(
            "Select Resources",
            options=list(resource_display_map.values()),
            default=["Patient"]
        )
        
        # Convert display names back to IDs
        reverse_map = {v: k for k, v in resource_display_map.items()}
        selected_resources = [reverse_map[name] for name in selected_display_names]
        
        # --- FEATURE: Resource Suggestions (Safe to Remove) ---
        if selected_resources:
            try:
                dep_graph = DependencyGraph(get_enabled_resources())
                missing = dep_graph.get_missing_dependencies(selected_resources)
                
                if missing:
                    st.info(f"💡 **Tip**: Selected resources rely on: {', '.join([resource_display_map.get(m, m) for m in missing])}")
                    if st.button("Add Missing Dependencies"):
                        # Logic to update selection would go here, but for now we just show the tip
                        # To truly update multiselect programmatically requires Session State callbacks
                        # which is more complex. For now, the tip is sufficient value.
                        st.warning("Please manually select the missing resources above.")
            except Exception as e:
                # Fail silently to not crash the app
                pass
        # ------------------------------------------------------
        st.markdown("### 🔢 Record Counts")
        granular_counts = {}
        if selected_resources:
            for res in selected_resources:
                # Use a specific key for each resource to maintain state
                # --- FEATURE: Smart Record Count Suggestions ---
                default_count = 5
                config = get_resource_config(res)
                smart_ratio = config.get("smart_ratio", 1.0)
                
                # Check if we have a parent to base the count on
                dep_graph = DependencyGraph(get_enabled_resources())
                parents = dep_graph.get_parents(res)
                suggested_count_msg = ""
                
                if parents:
                    # Just pick the first parent found in the selection to be the driver
                    # Ideally we might let user pick the driver, but simple is better here.
                    for p in parents:
                        if p in selected_resources and p in granular_counts:
                            parent_count = granular_counts[p]
                            calc_count = int(parent_count * smart_ratio)
                            if calc_count != default_count:
                                default_count = calc_count
                                suggested_count_msg = f" (Suggested: {calc_count} based on {resource_display_map.get(p, p)})"
                            break
                            
                granular_counts[res] = st.number_input(
                    f"Count for {resource_display_map.get(res, res)}{suggested_count_msg}:",
                    min_value=1,
                    max_value=100,
                    value=default_count,
                    key=f"count_{res}"
                )
                # -----------------------------------------------
        else:
            st.info("Select resources to set counts.")
    
    with col2:
        st.markdown("### ⚡ Quick Inputs (Optional)")
        
        quick_inputs = {}
        
        # Age range
        age_col1, age_col2 = st.columns(2)
        with age_col1:
            age_min = st.number_input("Min Age", min_value=0, max_value=120, value=18)
        with age_col2:
            age_max = st.number_input("Max Age", min_value=0, max_value=120, value=65)
        
        if age_min > 0 or age_max < 120:
            quick_inputs["age_min"] = age_min
            quick_inputs["age_max"] = age_max
        
        # Gender
        gender = st.selectbox(
            "Gender",
            options=["Any"] + QUICK_INPUT_OPTIONS["gender"],
            index=0
        )
        if gender != "Any":
            quick_inputs["gender"] = gender
        
        # State
        state = st.selectbox(
            "State",
            options=["Any"] + QUICK_INPUT_OPTIONS["states"],
            index=0
        )
        if state != "Any":
            quick_inputs["state"] = state
        
        # Insurance Type
        insurance = st.selectbox(
            "Insurance Type",
            options=["Any"] + QUICK_INPUT_OPTIONS["insurance_types"],
            index=0
        )
        if insurance != "Any":
            quick_inputs["insurance_type"] = insurance
    
    # LLM Settings (collapsible)
    with st.expander("🎛️ LLM Settings"):
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=LLM_SETTINGS["default_temperature"],
            step=0.1,
            help="Higher = more creative, Lower = more precise"
        )
        
        max_tokens = st.slider(
            "Max Tokens",
            min_value=500,
            max_value=8000,
            value=LLM_SETTINGS["default_max_tokens"],
            step=500
        )
    
    # Output Options
    with st.expander("📤 Output Options"):
        apply_md5 = st.checkbox("Apply MD5 hashing to PHI fields", value=True)
        validate_output = st.checkbox("Validate generated data", value=True)
        use_session_context = st.checkbox("🔄 Use existing session data as context", value=True, help="Tells the AI to maintain consistency with previously generated records in this session.")
        
        if st.session_state.session_history:
            if st.button("🗑️ Clear Session History"):
                st.session_state.session_history = {}
                st.success("Session history cleared!")
                st.rerun()
    
    st.divider()
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_clicked = st.button(
            "🚀 Generate Data",
            type="primary",
            use_container_width=True,
            disabled=not selected_resources
        )
    
    if generate_clicked:
        if not user_prompt.strip():
            st.warning("Please enter a prompt describing what data to generate.")
            return
        
        with st.spinner("Generating synthetic data..."):
            try:
                logger.info(f"Generation request: {user_prompt[:50]}... Resources: {selected_resources}")
                
                # Generate data
                generator = TableGenerator()
                results = generator.generate(
                    user_prompt=user_prompt,
                    resources=selected_resources,
                    record_count=granular_counts,
                    quick_inputs=quick_inputs if quick_inputs else None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    session_context=st.session_state.session_history if use_session_context else None
                )
                
                # Process results
                all_data = {}
                for resource, result in results.items():
                    if result.success:
                        data = result.data
                        
                        # Apply MD5 if requested
                        if apply_md5:
                            config = get_resource_config(resource)
                            md5_fields = config.get("md5_fields", [])
                            if md5_fields:
                                hasher = MD5Hasher()
                                data = hasher.hash_fields(data, md5_fields)
                        
                        # Validate if requested
                        if validate_output:
                            validation = validate_data(data)
                            if not validation.valid:
                                logger.warning(f"Validation errors for {resource}: {len(validation.errors)}")
                                st.warning(f"{resource}: {len(validation.errors)} validation errors")
                        
                        all_data[resource] = data
                        logger.info(f"Successfully generated {len(data)} records for {resource}")
                        st.success(f"✅ {resource}: Generated {len(data)} records")
                        
                        # Update session history
                        if resource not in st.session_state.session_history:
                            st.session_state.session_history[resource] = []
                        st.session_state.session_history[resource].extend(data)
                    else:
                        logger.error(f"Failed to generate {resource}: {result.error}")
                        st.error(f"❌ {resource}: {result.error}")
                
                # Store in session state
                st.session_state.generated_data = all_data
                st.session_state.generation_status = "success"
                
            except Exception as e:
                logger.exception("Fatal error during generation")
                st.error(f"Generation failed: {str(e)}")
                st.session_state.generation_status = "error"


def render_knowledge_tab():
    """Render knowledge base management tab"""
    st.markdown("### 📚 Knowledge Base Management")
    
    st.markdown("""
    Index your DDL files and guidelines to enable RAG-enhanced generation.
    
    **Folder Structure:**
    - `ddl/` - DDL files (e.g., patient.sql)
    - `knowledge/` - Guidelines and documentation
    """)
    
    # Show current status
    enabled_resources = get_enabled_resources()
    
    for resource in enabled_resources:
        config = get_resource_config(resource)
        ddl_file = config.get("ddl_file", "")
        knowledge_dir = config.get("knowledge_dir", "")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            ddl_exists = os.path.exists(ddl_file)
            status = "✅" if ddl_exists else "❌"
            st.markdown(f"**{config['display_name']}** DDL: {status}")
        
        with col2:
            knowledge_exists = os.path.exists(knowledge_dir) and any(Path(knowledge_dir).iterdir()) if os.path.exists(knowledge_dir) else False
            status = "✅" if knowledge_exists else "⚪"
            st.markdown(f"Guidelines: {status}")
        
        with col3:
            if st.button(f"Index", key=f"index_{resource}"):
                with st.spinner(f"Indexing {resource}..."):
                    count = index_resource(resource)
                    st.success(f"Indexed {count} chunks")
    
    st.divider()
    
    # Upload documents
    st.markdown("### 📤 Upload Documents")
    uploaded_file = st.file_uploader(
        "Upload guidelines (TXT, PDF, CSV)",
        type=["txt", "pdf", "csv"],
        key="doc_upload"
    )
    
    if uploaded_file:
        target_resource = st.selectbox(
            "Target Resource",
            options=["global"] + enabled_resources,
            key="upload_target"
        )
        
        if st.button("Upload & Index"):
            # Save file
            target_dir = Path("knowledge") / target_resource
            target_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = target_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"Saved to {file_path}")
            
            # Index
            with st.spinner("Indexing..."):
                retriever = get_retriever()
                count = retriever.index_directory(str(target_dir), target_resource)
                st.success(f"Indexed {count} chunks")


def render_results_tab():
    """Render results and export tab"""
    st.markdown("### 📊 Generated Results")
    
    if st.session_state.generated_data:
        data = st.session_state.generated_data
        
        for resource, records in data.items():
            st.markdown(f"#### {resource.title()} ({len(records)} records)")
            
            # Show preview
            if records:
                # Convert to displayable format
                display_data = []
                for record in records[:10]:  # Show first 10
                    display_record = {}
                    for k, v in record.items():
                        if isinstance(v, (dict, list)):
                            display_record[k] = json.dumps(v)[:100] + "..." if len(json.dumps(v)) > 100 else json.dumps(v)
                        elif isinstance(v, int) and (v > 9007199254740991 or v < -9007199254740991):
                            # Convert large integers to string to avoid OverflowError in st.dataframe
                            # Using JavaScript's Number.MAX_SAFE_INTEGER as a conservative threshold
                            display_record[k] = str(v)
                        else:
                            display_record[k] = v
                    display_data.append(display_record)
                
                st.dataframe(display_data, use_container_width=True)
                
                # Export button
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📥 Export {resource} to CSV", key=f"export_{resource}"):
                        exporter = CSVExporter()
                        filepath = exporter.export(records, resource)
                        st.success(f"Exported to: {filepath}")
                        
                        # Download button
                        with open(filepath, "r") as f:
                            csv_content = f.read()
                        st.download_button(
                            "Download CSV",
                            csv_content,
                            file_name=f"{resource}_synthetic.csv",
                            mime="text/csv",
                            key=f"download_{resource}"
                        )
                
                with col2:
                    if st.button(f"📋 Copy JSON", key=f"json_{resource}"):
                        st.code(json.dumps(records[:5], indent=2), language="json")
            
            st.divider()
    else:
        st.info("No data generated yet. Go to the Generate tab to create synthetic data.")


def index_resource(resource: str) -> int:
    """Index a single resource's DDL and guidelines"""
    config = get_resource_config(resource)
    retriever = get_retriever()
    total = 0
    
    # Index DDL
    ddl_file = config.get("ddl_file", "")
    if os.path.exists(ddl_file):
        count = retriever.index_ddl(ddl_file, resource)
        total += count
    
    # Index guidelines
    knowledge_dir = config.get("knowledge_dir", "")
    if os.path.exists(knowledge_dir):
        count = retriever.index_directory(knowledge_dir, resource)
        total += count
    
    return total


def index_all_resources():
    """Index all enabled resources"""
    for resource in get_enabled_resources():
        index_resource(resource)
    
    # Index global knowledge
    global_dir = "knowledge/global"
    if os.path.exists(global_dir):
        retriever = get_retriever()
        retriever.index_directory(global_dir, "global")


def main():
    """Main entry point"""
    init_session_state()
    render_sidebar()
    render_main_ui()


if __name__ == "__main__":
    main()
