import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import base64
from datetime import datetime

import database as db
import api_utils as api

# Page configuration
st.set_page_config(
    page_title="Research Decision Tracker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
db.init_db()

# Load Custom CSS
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("styles.css")

# Session State Initialization
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None
if "active_project_name" not in st.session_state:
    st.session_state.active_project_name = None

# Header styling
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
    <div>
        <h1 style="margin:0; font-weight:700; color:#F8FAFC;">🔍 Research Decision Tracker</h1>
        <p style="margin:0; color:#94A3B8; font-size:16px;">Local-first flight recorder for documenting and visualizing academic literature reviews.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Project Selection
st.sidebar.markdown("<h2 style='margin-top:0;'>📁 Projects</h2>", unsafe_allow_html=True)

# Fetch projects
projects = db.get_projects()

if not projects:
    st.sidebar.warning("No projects found. Please create one.")
    new_proj_name = st.sidebar.text_input("New Project Name")
    new_proj_desc = st.sidebar.text_area("Description")
    if st.sidebar.button("Create Project", key="init_create_proj", use_container_width=True):
        if new_proj_name.strip():
            pid = db.create_project(new_proj_name.strip(), new_proj_desc.strip())
            if pid:
                st.session_state.active_project_id = pid
                st.session_state.active_project_name = new_proj_name.strip()
                st.sidebar.success(f"Project '{new_proj_name}' created!")
                st.rerun()
            else:
                st.sidebar.error("Project name must be unique.")
        else:
            st.sidebar.error("Project name cannot be empty.")
else:
    # Project selector
    project_options = {p['name']: p['id'] for p in projects}
    selected_proj_name = st.sidebar.selectbox(
        "Active Project",
        options=list(project_options.keys()),
        index=0 if st.session_state.active_project_name not in project_options else list(project_options.keys()).index(st.session_state.active_project_name)
    )
    
    st.session_state.active_project_id = project_options[selected_proj_name]
    st.session_state.active_project_name = selected_proj_name
    
    # Manage projects button/expander
    with st.sidebar.expander("➕ Create / Manage Projects"):
        st.markdown("### Create New Project")
        new_proj_name = st.text_input("Project Name", key="new_proj_name")
        new_proj_desc = st.text_area("Description", key="new_proj_desc")
        if st.button("Create", key="create_proj", use_container_width=True):
            if new_proj_name.strip():
                pid = db.create_project(new_proj_name.strip(), new_proj_desc.strip())
                if pid:
                    st.session_state.active_project_id = pid
                    st.session_state.active_project_name = new_proj_name.strip()
                    st.success(f"Project '{new_proj_name}' created!")
                    st.rerun()
                else:
                    st.error("Project name must be unique.")
            else:
                st.error("Project name cannot be empty.")
        
        st.markdown("---")
        st.markdown("### Delete Project")
        del_proj = st.selectbox("Select Project to Delete", options=list(project_options.keys()), key="del_proj_select")
        if st.button("Delete Active Project", key="delete_proj_btn", use_container_width=True, type="secondary"):
            db.delete_project(project_options[del_proj])
            st.session_state.active_project_id = None
            st.session_state.active_project_name = None
            st.success(f"Deleted project '{del_proj}'")
            st.rerun()

st.sidebar.markdown("---")

# Navigation Menu
menu = ["📊 Dashboard", "📝 Search & Log Resources", "🕸️ Visual Path (DAG)", "📅 Timeline Journal", "📤 Export & Citation"]
choice = st.sidebar.radio("Navigation", menu)

# Ensure project is selected
if st.session_state.active_project_id is None:
    st.info("👈 Please create or select a project in the sidebar to begin.")
else:
    active_pid = st.session_state.active_project_id
    project_details = db.get_project(active_pid)
    
    # Display project header summary
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.25); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 12px 16px; margin-bottom: 24px;">
        <span style="font-size: 12px; font-weight:600; text-transform:uppercase; color:#8B5CF6; letter-spacing:0.05em;">Active Project</span>
        <h3 style="margin: 4px 0 0 0; color:#F1F5F9;">{project_details['name']}</h3>
        <p style="margin: 4px 0 0 0; font-size:14px; color:#94A3B8;">{project_details['description'] or 'No description provided.'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ------------------ PAGES ------------------
    if choice == "📊 Dashboard":
        st.subheader("Project Dashboard")
        
        # Get metrics
        analytics = db.get_analytics(active_pid)
        decisions = analytics["decisions"]
        
        selected_count = decisions.get("Selected", 0)
        rejected_count = decisions.get("Rejected", 0)
        deferred_count = decisions.get("Deferred", 0)
        total_queries = analytics["queries_count"]
        total_resources = selected_count + rejected_count + deferred_count + analytics["unevaluated"]
        
        # Row 1: Metrics Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value metric-queries">{total_queries}</div>
                <div style="font-size:13px; color:#94A3B8; font-weight:500;">Search Queries Logged</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#F1F5F9;">{total_resources}</div>
                <div style="font-size:13px; color:#94A3B8; font-weight:500;">Total Resources Found</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value metric-selected">{selected_count}</div>
                <div style="font-size:13px; color:#94A3B8; font-weight:500;">Papers Selected</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value metric-rejected">{rejected_count}</div>
                <div style="font-size:13px; color:#94A3B8; font-weight:500;">Papers Rejected</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value metric-deferred">{deferred_count}</div>
                <div style="font-size:13px; color:#94A3B8; font-weight:500;">Papers Deferred</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: Charts and recent queries
        chart_col, details_col = st.columns([3, 2])
        
        with chart_col:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Resource Decisions Breakdown")
            if total_resources > 0:
                labels = ['Selected', 'Rejected', 'Deferred', 'Unevaluated']
                values = [selected_count, rejected_count, deferred_count, analytics["unevaluated"]]
                colors = ['#10B981', '#EF4444', '#F59E0B', '#6B7280']
                
                # Filter out zeroes for a cleaner chart
                filtered_labels = [l for l, v in zip(labels, values) if v > 0]
                filtered_values = [v for v in values if v > 0]
                filtered_colors = [c for c, v in zip(colors, values) if v > 0]
                
                fig = go.Figure(data=[go.Pie(
                    labels=filtered_labels,
                    values=filtered_values,
                    hole=.4,
                    marker=dict(colors=filtered_colors, line=dict(color='#0F172A', width=2))
                )])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#F8FAFC',
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=300,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No resources added yet. Go to 'Search & Log Resources' to populate your workspace.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with details_col:
            st.markdown('<div class="glass-card" style="height: 380px; overflow-y: auto;">', unsafe_allow_html=True)
            st.markdown("### Recent Search Queries")
            queries = db.get_queries(active_pid)
            if queries:
                for q in queries[:5]:
                    st.markdown(f"""
                    <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding: 10px 0;">
                        <div style="font-weight: 600; color: #F1F5F9;">🔍 {q['query_text']}</div>
                        <div style="font-size:12px; color:#94A3B8;">Engine: {q['engine']} | Logged: {q['created_at'][:16]}</div>
                        {f'<div style="font-size:13px; color:#CBD5E1; font-style:italic; margin-top:4px;">Note: {q["notes"]}</div>' if q['notes'] else ''}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No search queries logged yet.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Scope shifts log
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Scope Shifts & Key Milestones")
        with st.form("scope_shift_form", clear_on_submit=True):
            st.markdown("Document changes in your research questions, directions, or key definitions.")
            scope_desc = st.text_area("Describe the scope change / milestone", placeholder="e.g., Narrowed thesis scope to only consider local-first applications after recognizing security trade-offs in cloud models.")
            submitted = st.form_submit_button("Record Milestone", type="primary")
            if submitted and scope_desc.strip():
                db.log_scope_change(active_pid, scope_desc.strip())
                st.success("Milestone recorded!")
                st.rerun()
                
        # List milestones
        timeline_events = db.get_timeline(active_pid)
        milestones = [e for e in timeline_events if e['event_type'] == 'SCOPE_CHANGED']
        if milestones:
            st.markdown("#### Documented Scope Milestones")
            for m in milestones:
                st.markdown(f"""
                <div style="background: rgba(139, 92, 246, 0.08); border-left: 4px solid #8B5CF6; padding: 12px; border-radius: 4px; margin-bottom: 10px;">
                    <div style="font-size: 12px; color: #94A3B8;">Recorded: {m['created_at'][:16]}</div>
                    <div style="color: #E2E8F0; font-weight: 500; margin-top: 4px;">{m['description']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------ SEARCH & LOG RESOURCES ------------------
    elif choice == "📝 Search & Log Resources":
        st.subheader("Log Research Activities & Papers")
        
        # Two modes: Search & API, or Manual Entry
        tab_api, tab_manual = st.tabs(["🔍 Search API / Lookup DOI", "✍️ Manual Entry & Log Query"])
        
        with tab_api:
            st.markdown("#### Look up literature using open-access databases")
            
            # Step 1: Log query
            api_choice = st.selectbox("Select Database API", ["OpenAlex (Cross-disciplinary & Open)", "arXiv (Physics, CS, Math, Bio)"])
            search_input = st.text_input("Enter Search Terms or DOI", placeholder="e.g. Local-first databases, or 10.1145/3475738")
            
            col_search_btn, col_skip_btn = st.columns([1, 4])
            with col_search_btn:
                search_clicked = st.button("Search & Log", type="primary", use_container_width=True)
            
            if search_clicked and search_input.strip():
                query_text = search_input.strip()
                
                # Check if it's a DOI
                is_doi = ("10." in query_text) and ("/" in query_text)
                
                st.markdown("---")
                with st.spinner("Fetching papers..."):
                    # Log search query in SQL
                    qid = db.log_query(active_pid, query_text, api_choice, "Search initiated via API.")
                    
                    # Fetch
                    if is_doi:
                        st.info("DOI detected. Resolving metadata...")
                        resolved_paper = api.resolve_doi_openalex(query_text)
                        results = [resolved_paper] if resolved_paper else []
                    else:
                        if api_choice.startswith("OpenAlex"):
                            results = api.search_openalex(query_text, limit=6)
                        else:
                            results = api.search_arxiv(query_text, limit=6)
                            
                if not results:
                    st.warning("No results found. Please check spelling or check network connection.")
                else:
                    st.success(f"Found {len(results)} matches! Select which papers to record:")
                    
                    for i, r in enumerate(results):
                        # Unique identifier for dynamic streamlit session mapping
                        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
                        st.markdown(f"### {r['title']}")
                        st.markdown(f"**Authors**: {r['authors']} | **Venue**: {r['journal']} ({r['year']})")
                        with st.expander("📖 Abstract"):
                            st.write(r['abstract'])
                        
                        # Add paper to tracker button
                        if st.button(f"📥 Log Paper to Workspace", key=f"add_api_paper_{i}"):
                            rid = db.add_resource(
                                project_id=active_pid,
                                title=r['title'],
                                authors=r['authors'],
                                journal=r['journal'],
                                year=r['year'],
                                url=r['url'],
                                doi=r['doi'],
                                abstract=r['abstract'],
                                source_query_id=qid
                            )
                            st.success(f"Paper '{r['title']}' saved to database!")
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        with tab_manual:
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("#### Record a Search Query (No API)")
                with st.form("manual_query_form"):
                    q_text = st.text_input("Search query used", placeholder="e.g., SQLite versus DuckDB performance benchmark")
                    q_eng = st.selectbox("Search engine used", ["Google Scholar", "Google", "IEEE Xplore", "ACM DL", "Scopus", "Other"])
                    q_note = st.text_area("Search notes / initial impression", placeholder="Found many relevant papers, but mostly focused on cloud DBs. Narrowed down results.")
                    q_sub = st.form_submit_button("Log Query", type="primary")
                    if q_sub and q_text.strip():
                        db.log_query(active_pid, q_text.strip(), q_eng, q_note.strip())
                        st.success("Query logged!")
                        st.rerun()
            with col_r:
                st.markdown("#### Record a Paper Manually")
                with st.form("manual_paper_form"):
                    p_title = st.text_input("Paper Title *")
                    p_authors = st.text_input("Authors")
                    p_journal = st.text_input("Journal / Conference")
                    p_year = st.number_input("Publication Year", min_value=1800, max_value=2030, value=2026)
                    p_url = st.text_input("URL")
                    p_doi = st.text_input("DOI")
                    p_abstract = st.text_area("Abstract / Summary")
                    
                    # Associate with a logged query
                    queries = db.get_queries(active_pid)
                    query_options = {"None (Manual Add)": None}
                    for q in queries:
                        query_options[f"[{q['created_at'][:10]}] {q['query_text'][:40]}"] = q['id']
                    
                    assoc_q = st.selectbox("Source Query", options=list(query_options.keys()))
                    
                    p_sub = st.form_submit_button("Record Paper", type="primary")
                    if p_sub and p_title.strip():
                        db.add_resource(
                            project_id=active_pid,
                            title=p_title.strip(),
                            authors=p_authors.strip(),
                            journal=p_journal.strip(),
                            year=int(p_year),
                            url=p_url.strip(),
                            doi=p_doi.strip(),
                            abstract=p_abstract.strip(),
                            source_query_id=query_options[assoc_q]
                        )
                        st.success(f"Paper '{p_title}' recorded!")
                        st.rerun()
                        
        # Section 2: Manage & Evaluate papers in Project Workspace
        st.markdown("---")
        st.subheader("📁 Review & Decide on Logged Papers")
        
        resources = db.get_resources(active_pid)
        if not resources:
            st.info("No papers logged in this project workspace yet. Use search parameters above to log papers.")
        else:
            for idx, res in enumerate(resources):
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                
                # Header with status badge
                badge_class = "badge-unevaluated"
                status_str = "Unevaluated"
                if res['status']:
                    status_str = res['status']
                    badge_class = f"badge-{status_str.lower()}"
                
                col_title, col_status = st.columns([4, 1])
                with col_title:
                    st.markdown(f"#### {res['title']}")
                with col_status:
                    st.markdown(f'<div style="text-align:right;"><span class="badge {badge_class}">{status_str}</span></div>', unsafe_allow_html=True)
                
                st.markdown(f"**Authors**: {res['authors']} | **Journal/Venue**: {res['journal']} ({res['year']})")
                if res['url']:
                    st.markdown(f"[Link to Document]({res['url']}) | DOI: {res['doi'] or 'N/A'}")
                
                with st.expander("📖 View Abstract"):
                    st.write(res['abstract'])
                
                # Decision panel
                with st.expander("📝 Make / Update Research Decision"):
                    with st.form(f"decision_form_{idx}"):
                        dec_status = st.selectbox("Decision Status", ["Selected", "Rejected", "Deferred"], 
                                                  index=0 if not res['status'] else ["Selected", "Rejected", "Deferred"].index(res['status']))
                        dec_just = st.text_area("Justification / Why is this decision being made?", 
                                                value=res['justification'] or "", 
                                                placeholder="Explain how this paper fits your work, or why it was rejected. E.g. 'Highly relevant methodology, using Vis.js for visual DAG representations.'")
                        dec_notes = st.text_area("Additional internal notes / thoughts", 
                                                 value=res['decision_notes'] or "")
                        
                        dec_btn = st.form_submit_button("Record Decision")
                        if dec_btn:
                            if not dec_just.strip():
                                st.error("Please provide a justification for your decision.")
                            else:
                                success = db.record_decision(res['id'], dec_status, dec_just.strip(), dec_notes.strip())
                                if success:
                                    st.success(f"Decision '{dec_status}' saved!")
                                    st.rerun()
                                    
                if res['status']:
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.03); border-radius: 4px; padding: 10px; margin-top: 10px; border-left: 3px solid #64748B;">
                        <strong>Decision Justification</strong>: {res['justification']}<br>
                        {f'<strong>Notes</strong>: {res["decision_notes"]}' if res['decision_notes'] else ''}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # ------------------ VISUAL PATH (DAG) ------------------
    elif choice == "🕸️ Visual Path (DAG)":
        st.subheader("Interactive Research Path Visualizer")
        st.markdown("This graph maps out your literature review flight path. It shows the relationship between your research questions/queries (blue) and the papers you explored, colored by decision status: **Selected** (green), **Rejected** (red), **Deferred** (yellow), and **Unevaluated** (grey).")
        
        # Load resources and queries
        queries = db.get_queries(active_pid)
        resources = db.get_resources(active_pid)
        
        if not queries and not resources:
            st.info("Log some queries and papers first to generate the visual path graph!")
        else:
            # Prepare Nodes and Edges for Vis.js
            nodes_data = []
            edges_data = []
            
            # 1. Project node (root)
            nodes_data.append({
                "id": "proj_root",
                "label": f"Project: {st.session_state.active_project_name}",
                "shape": "star",
                "color": "#8B5CF6",
                "size": 25,
                "title": f"Root project container for {st.session_state.active_project_name}"
            })
            
            # 2. Add queries
            for q in queries:
                nodes_data.append({
                    "id": f"query_{q['id']}",
                    "label": f"🔍 {q['query_text'][:30]}...",
                    "shape": "box",
                    "color": "#1E3A8A",
                    "title": f"Query: {q['query_text']}\nEngine: {q['engine']}\nDate: {q['created_at'][:10]}"
                })
                # Connect query to project root
                edges_data.append({
                    "from": "proj_root",
                    "to": f"query_{q['id']}"
                })
                
            # 3. Add resources
            for r in resources:
                # Determine color by status
                status = r['status']
                if status == 'Selected':
                    color = '#10B981'
                elif status == 'Rejected':
                    color = '#EF4444'
                elif status == 'Deferred':
                    color = '#F59E0B'
                else:
                    color = '#6B7280' # Unevaluated
                    
                title_clean = r['title'].replace('"', '\\"').replace('\n', ' ')
                label_text = f"📄 {title_clean[:25]}..."
                
                # Tooltip text
                tooltip = f"Title: {r['title']}\nAuthors: {r['authors']}\nStatus: {status or 'Unevaluated'}"
                if r['justification']:
                    tooltip += f"\nJustification: {r['justification']}"
                
                nodes_data.append({
                    "id": f"resource_{r['id']}",
                    "label": label_text,
                    "shape": "dot",
                    "size": 18,
                    "color": color,
                    "title": tooltip
                })
                
                # Connect resource to parent query or project root
                if r['source_query_id']:
                    edges_data.append({
                        "from": f"query_{r['source_query_id']}",
                        "to": f"resource_{r['id']}"
                    })
                else:
                    edges_data.append({
                        "from": "proj_root",
                        "to": f"resource_{r['id']}"
                    })
                    
            # Generate the Custom HTML for Vis.js
            nodes_json = json.dumps(nodes_data)
            edges_json = json.dumps(edges_data)
            
            vis_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
              <style type="text/css">
                body {{
                  background-color: #0B0F19; /* Sleek dark theme bg */
                  color: #F8FAFC;
                  font-family: 'Inter', sans-serif;
                  margin: 0;
                  padding: 0;
                  overflow: hidden;
                }}
                #mynetwork {{
                  width: 100%;
                  height: 600px;
                  border: 1px solid rgba(255, 255, 255, 0.08);
                  background-color: #0F172A;
                  border-radius: 12px;
                }}
              </style>
            </head>
            <body>
              <div id="mynetwork"></div>
              <script type="text/javascript">
                var nodes = new vis.DataSet({nodes_json});
                var edges = new vis.DataSet({edges_json});
                var container = document.getElementById('mynetwork');
                var data = {{
                  nodes: nodes,
                  edges: edges
                }};
                var options = {{
                  nodes: {{
                    font: {{
                      color: '#F8FAFC',
                      size: 13,
                      face: 'Inter'
                    }},
                    borderWidth: 2,
                    shadow: true
                  }},
                  edges: {{
                    color: {{ color: '#475569', highlight: '#8B5CF6', hover: '#8B5CF6' }},
                    width: 2,
                    arrows: {{
                      to: {{ enabled: true, scaleFactor: 0.5 }}
                    }},
                    smooth: {{
                      type: 'continuous',
                      roundness: 0.5
                    }}
                  }},
                  interaction: {{
                    hover: true,
                    tooltipDelay: 150
                  }},
                  physics: {{
                    barnesHut: {{
                      gravitationalConstant: -1800,
                      centralGravity: 0.2,
                      springLength: 120,
                      springConstant: 0.05,
                      damping: 0.09,
                      avoidOverlap: 0.2
                    }},
                    solver: 'barnesHut'
                  }}
                }};
                var network = new vis.Network(container, data, options);
              </script>
            </body>
            </html>
            """
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.components.v1.html(vis_html, height=620)
            st.markdown('</div>', unsafe_allow_html=True)

    # ------------------ TIMELINE JOURNAL ------------------
    elif choice == "📅 Timeline Journal":
        st.subheader("Chronological Research Journal")
        st.markdown("The chronological flight-recorder timeline of all your research queries, papers, and decisions. Great for reviewing your journey or sharing with advisors.")
        
        timeline_events = db.get_timeline(active_pid)
        
        if not timeline_events:
            st.info("No events in the timeline yet. Start by logging search queries or recording decisions.")
        else:
            st.markdown('<div class="glass-card" style="padding-top: 30px;">', unsafe_allow_html=True)
            for event in timeline_events:
                # Choose color or icon based on event type
                event_type = event['event_type']
                icon = "⚙️"
                color_glow = "#6B7280"
                
                if event_type == 'PROJECT_CREATED':
                    icon = "📁"
                    color_glow = "#8B5CF6"
                elif event_type == 'QUERY_LOGGED':
                    icon = "🔍"
                    color_glow = "#3B82F6"
                elif event_type == 'RESOURCE_ADDED':
                    icon = "📄"
                    color_glow = "#9CA3AF"
                elif event_type == 'DECISION_MADE':
                    icon = "⚖️"
                    # Determine color from decision string in description
                    if "Selected" in event['description']:
                        color_glow = "#10B981"
                        icon = "✅"
                    elif "Rejected" in event['description']:
                        color_glow = "#EF4444"
                        icon = "❌"
                    elif "Deferred" in event['description']:
                        color_glow = "#F59E0B"
                        icon = "⏳"
                elif event_type == 'SCOPE_CHANGED':
                    icon = "🎯"
                    color_glow = "#EC4899"
                    
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-dot" style="background-color: {color_glow}; box-shadow: 0 0 10px {color_glow};"></div>
                    <div class="timeline-date">{event['created_at']}</div>
                    <div class="timeline-title">{icon} {event_type.replace('_', ' ')}</div>
                    <div style="color:#CBD5E1; font-size:14px; margin-top:4px;">{event['description']}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ------------------ EXPORT & CITATION ------------------
    elif choice == "📤 Export & Citation":
        st.subheader("Export Workspace & Citations")
        
        resources = db.get_resources(active_pid)
        queries = db.get_queries(active_pid)
        timeline = db.get_timeline(active_pid)
        
        tab_md, tab_bib = st.tabs(["📝 Markdown Report", "📚 BibTeX Citations"])
        
        with tab_md:
            st.markdown("### Generate Markdown Research Journal")
            st.markdown("This will generate a structured markdown report including all logged search queries, evaluation rationales, scope adjustments, and final selections.")
            
            # Compile markdown
            md_report = f"# Research Decision Log: {project_details['name']}\n"
            md_report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            md_report += f"## Description\n{project_details['description'] or 'No description provided.'}\n\n"
            
            md_report += "## Search Queries History\n"
            if queries:
                for q in queries:
                    md_report += f"- **Query**: `{q['query_text']}` (Engine: {q['engine']}) on {q['created_at'][:16]}\n"
                    if q['notes']:
                        md_report += f"  - *Note*: {q['notes']}\n"
            else:
                md_report += "No search queries logged.\n"
            md_report += "\n"
            
            md_report += "## Literature Summary & Decisions\n"
            if resources:
                for r in resources:
                    status = r['status'] or "Unevaluated"
                    md_report += f"### {r['title']}\n"
                    md_report += f"- **Authors**: {r['authors']}\n"
                    md_report += f"- **Venue/Year**: {r['journal']} ({r['year']})\n"
                    md_report += f"- **Status**: `{status.upper()}`\n"
                    if r['url']:
                        md_report += f"- **URL**: {r['url']}\n"
                    if r['doi']:
                        md_report += f"- **DOI**: {r['doi']}\n"
                    if r['justification']:
                        md_report += f"- **Justification**: {r['justification']}\n"
                    if r['decision_notes']:
                        md_report += f"- **Decision Notes**: {r['decision_notes']}\n"
                    md_report += "\n"
            else:
                md_report += "No papers evaluated.\n"
                
            st.text_area("Preview Markdown Report", value=md_report, height=350)
            
            b64_md = base64.b64encode(md_report.encode()).decode()
            href_md = f'<a href="data:file/markdown;base64,{b64_md}" download="research_report_{active_pid}.md" style="text-decoration:none;"><button class="glow-btn" style="background-color:#8B5CF6; color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:600; cursor:pointer;">📥 Download Report (.md)</button></a>'
            st.markdown(href_md, unsafe_allow_html=True)
            
        with tab_bib:
            st.markdown("### Generate BibTeX File")
            st.markdown("Generates standard BibTeX citations for all papers marked as **Selected**.")
            
            selected_papers = [r for r in resources if r['status'] == 'Selected']
            
            if not selected_papers:
                st.warning("No papers have been marked as 'Selected' yet. Change paper decision status to 'Selected' to generate bibliography.")
                bib_content = "% No papers selected."
            else:
                bib_content = ""
                for r in selected_papers:
                    # Generate citekey
                    author_last = "unknown"
                    if r['authors']:
                        author_last = r['authors'].split(',')[0].split(' ')[-1].lower().replace('et', '').replace('al.', '').strip()
                        if not author_last:
                            author_last = "ref"
                    year_val = r['year'] or "2026"
                    title_first_word = r['title'].split(' ')[0].lower().replace(':', '').replace(',', '')
                    citekey = f"{author_last}{year_val}{title_first_word}"
                    
                    bib_content += f"@article{{{citekey},\n"
                    bib_content += f"  title = {{{r['title']}}},\n"
                    bib_content += f"  author = {{{r['authors']}}},\n"
                    bib_content += f"  journal = {{{r['journal']}}},\n"
                    bib_content += f"  year = {{{year_val}}},\n"
                    if r['doi']:
                        bib_content += f"  doi = {{{r['doi']}}},\n"
                    if r['url']:
                        bib_content += f"  url = {{{r['url']}}},\n"
                    bib_content += "}\n\n"
                    
            st.text_area("Preview BibTeX citations", value=bib_content, height=350)
            
            if selected_papers:
                b64_bib = base64.b64encode(bib_content.encode()).decode()
                href_bib = f'<a href="data:file/bibtex;base64,{b64_bib}" download="bibliography_{active_pid}.bib" style="text-decoration:none;"><button class="glow-btn" style="background-color:#10B981; color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:600; cursor:pointer;">📥 Download Citations (.bib)</button></a>'
                st.markdown(href_bib, unsafe_allow_html=True)
