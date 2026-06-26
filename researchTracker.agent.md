Project Title: Research Decision Tracker
Project Description:
Research Decision Tracker is a lightweight application designed to help student researchers document and visualize their research process. The goal is not to recommend papers or direct research toward a specific conclusion. Instead, the application serves as a research journal that records how a researcher arrived at their decisions throughout a project.
Modern AI tools and search engines can generate large numbers of articles, summaries, and recommendations within minutes. While this accelerates literature reviews, it can also make it difficult for researchers to remember why certain papers were selected, rejected, or revisited later in the research process. Important decisions are often lost, making it difficult to reconstruct the path that led to a final literature review or project direction.
The application addresses this problem by recording research activities as they occur. Users can create research projects, log search queries, record papers that were reviewed, and document the rationale behind decisions. Each action is automatically timestamped to create a chronological history of the research process.
Key Features:
- Create and manage research projects
- Record search queries and research questions
- Add papers, articles, and other resources
- Mark resources as Selected, Rejected, or Deferred
- Record decision justifications and notes
- Automatically timestamp all research activities
- View a chronological timeline of research decisions
- Track changes in project scope over time
- Preserve rejected resources for future reference
- **Visual Research Paths (DAG)**: View an interactive node-link graph showing how queries led to papers, and the decisions made on them.
- **Literature API Integration**: Query OpenAlex and arXiv APIs to look up and import metadata (title, authors, journal, abstract) automatically using a DOI or search term.
- **Bibliography & Log Export**: Export the complete research timeline and notes to Markdown and bibliography citations to BibTeX.
- **Research Analytics Dashboard**: Interactive charts showing review metrics, selection ratios, and search progress.
Example Use Case:
A student conducting a literature review may evaluate dozens of papers but only cite a small subset. The Research Decision Tracker preserves not only the papers that were selected but also those that were rejected and the reasons behind those decisions. This creates a transparent record of the research process and helps researchers justify their choices, revisit previously discarded resources, and better understand how their thinking evolved throughout a project.
Technical Scope (MVP):
Python backend
SQLite database
Streamlit web interface
Local-first architecture with no required AI API usage
Focus on research tracking, documentation, and visualization
Expected Outcome:
The final product will provide students with a practical tool for documenting research decisions, improving transparency, supporting reflection, and encouraging more structured participation in academic research. Rather than functioning as a search engine or AI assistant, the system acts as a "research flight recorder" that preserves the complete history of a research project.
 

