# Agents — CIVITAS

## Orchestrator
**Papel:** Planeja a abordagem geral e coordena entre especialistas.
**Como invocar:**
"Act as the Orchestrator. Review SPEC.md and CLAUDE.md, then create a
step-by-step implementation plan. Assign tasks to each specialist.
Output a task breakdown with dependencies."

## Backend Engineer
**Stack:** FastAPI, FAISS, NetworkX, PyVis, OpenCV, SQLite, Pytest
**Como invocar:**
"Act as the Backend Engineer. Implement [feature] using the CIVITAS stack.
Include Pytest tests. Follow the structure in research/backend/."

## Data Scientist / Graph Analyst
**Stack:** Pandas, GeoPandas, NetworkX, Matplotlib, Seaborn, Scikit-learn
**Como invocar:**
"Act as the Data Scientist. Analyze [dataset] from ISP-RJ.
Generate [analysis type]. Explain findings in Portuguese for the pitch."

## Frontend Engineer
**Stack:** React 18, Vite, Tailwind CSS, Leaflet, Recharts, PyVis HTML export
**Como invocar:**
"Act as the Frontend Engineer. Build [component].
Use Tailwind for all styling. Integrate with FastAPI at localhost:8000."

## Researcher
**Como invocar:**
"Act as the Researcher. Find [topic] relevant to Rio de Janeiro public safety.
For each finding: source URL, Portuguese summary, limitations, relevance rating.
Save to docs/RESEARCH.md."

## Presenter
**Como invocar:**
"Act as the Presenter. Generate a 5-minute pitch for CIVITAS.
Audience: Rio city officials + hackathon judges.
Write in Portuguese. Lead with the problem's human impact."
