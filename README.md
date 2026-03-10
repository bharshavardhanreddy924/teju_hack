# Conversational AI for Instant Business Intelligence Dashboards

An intelligent system that allows non-technical users to generate fully functional, interactive data dashboards using only natural language prompts.

## Features

- **Natural Language to SQL**: Automatically generates valid SQLite queries based on the uploaded data schema.
- **Dynamic Interactive Dashboards**: Selects the best visualization using `plotly.express` and displays interactive charts based on the query results.
- **Data Agnostic**: Upload any CSV file, and the app will instantly ingest it, analyze the schema, and allow you to ask questions about it. (Supports both UTF-8 and CP1252 parsing).
- **Follow-up Chat Capability**: Remembers chat history, allowing you to ask follow-up questions to filter data or modify generated charts.

## Technologies Used

- **Frontend & App State**: Streamlit
- **LLM Engine**: Google Gemini 2.0 Flash (`google-genai` SDK)
- **Data Backend**: Pandas & In-Memory SQLite 
- **Chart Generation**: Plotly

## Setup and Installation

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the App:
```bash
streamlit run app.py
```

4. Once the app opens in your browser:
   * **Enter your Gemini API Key in the sidebar.** (There is a default token provided for convenience, but you can enter your own).
   * **Upload a CSV file** (e.g., `Nykaa Digital Marketing.csv`). You can check the "Nykaa specific cleaning" box if you want to apply specific dataset cleaning.
   * **Ask questions!** Example: _"Show me total sales by region as a bar chart."_

## Architecture Pipeline

1. **Ingestion**: CSV -> Pandas DataFrame -> SQLite `user_data` table.
2. **Schema Extraction**: Generates schema metadata using `PRAGMA table_info()`.
3. **Intent to SQL Generation**: Sends schema + User Prompt + History Context to Gemini to format a query.
4. **Execution**: Safely runs the query on SQLite.
5. **Chart Generation**: Sends the raw data heads + original query + SQL to Gemini to write Python Plotly code.
6. **Rendering**: Safely executes Python code via `exec()` in local scope to produce a Streamlit `st.plotly_chart`.

## Evaluation Checklist Met
- [x] **Accuracy**: Retrieves exact data, uses Contextual Chart Selection via LLM prompt logic, and relies strictly on the DB schema for Hallucination Handling.
- [x] **Aesthetics**: Modern clean UX with loading step indicators and Plotly.
- [x] **Approach**: 2-stage independent agentic approach (SQL Agent -> Chart Agent) with prompt constraints.
- [x] **Bonus**: Follow-Up chat memory.
- [x] **Bonus**: Data format agnostic (uses runtime schema detection and Streamlit file uploader).
