<a id="HOMEWORK"></a>

# 📌 HOMEWORK

## Homework 2: AI Agent System with RAG and Tools

🕒 *Estimated Time: 3-4 hours*

---

## 📋 Homework Overview

Compile your work from the last 3 weeks into a complete **AI agent system** that combines multi-agent orchestration, RAG, and function calling.

This homework compiles work from:

- [`LAB_prompt_design.md`](../06_agents/LAB_prompt_design.md) — multi-agent prompt design
- [`LAB_custom_rag_query.md`](../07_rag/LAB_custom_rag_query.md) — RAG queries
- [`LAB_multi_agent_with_tools.md`](LAB_multi_agent_with_tools.md) — multi-agent systems with tools

**Note:** This homework compiles work from 3 weekly LABS. Each LAB represents the next step of your project. Show us your individual progress by compiling your work into a complete AI agent system.

---

## 🧭 Reference implementation in this repository (optional)

This repo includes a **self-contained worked example** under [`HW2/`](../HW2/README.md): two LLM steps, **function calling** into SQLite, a **deterministic retrieval JSON** (RAG-style payload), and a second model pass that writes a Markdown report. Full file map, outputs, troubleshooting, and optional **Shiny** UI are documented there.

If you use this reference code for your submission, you still need your **own writing**, **git links**, **screenshots**, and **documentation** as listed below.

### Concrete steps to run it (macOS / Linux)

Do these from your **clone of this repository** (adjust paths if your folder layout differs).

1. **Open a terminal** and go to the homework folder:

   ```bash
   cd HW2
   ```

2. **Pull the Ollama model** the code expects (default `llama3.2`). Use the provided script:

   ```bash
   chmod +x setup_hw2.sh    # first time only
   ./setup_hw2.sh
   ```

   - Requires [Ollama](https://ollama.com) installed and on your `PATH`.
   - To use another tag: `OLLAMA_MODEL=llama3.2:latest ./setup_hw2.sh`

3. **Confirm the database** `patients.db` is inside `HW2/`. If it is missing, from the repo root:

   ```bash
   cp 07_rag/patients.db HW2/patients.db
   ```

4. **Create a virtual environment and install Python packages:**

   ```bash
   cd HW2
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Run the Shiny app** (recommended; first run may take several minutes while the model loads):

   ```bash
   shiny run app/app.py --reload
   ```

   Use the in-app control to generate the clinical summary. Files also appear under `HW2/out/` (see the README).

6. **Alternative — CLI** (same pipeline as step 5, in the terminal):

   ```bash
   python clinical_pipeline.py
   ```

### Windows (short version)

- Install Ollama, then in **PowerShell**: `ollama pull llama3.2`
- Create the venv and install from `HW2/requirements.txt` as in [`HW2/README.md`](../HW2/README.md) (Windows sections).
- Run: `shiny run app/app.py --reload` from `HW2/` (or `python clinical_pipeline.py`).

### Where to read more

- **Primary doc:** [`HW2/README.md`](../HW2/README.md) — requirements, env vars, output table, troubleshooting, Shiny.
- **Pipeline module:** [`HW2/clinical_pipeline.py`](../HW2/clinical_pipeline.py)

---

## 📝 Instructions

### Who?

Individual homework assignment — 1 per team member.

### What?

Compile your work from the last 3 weeks into a complete **AI agent system** that demonstrates multi-agent orchestration, RAG integration, and function calling. **Submit a single .docx file.**

### Why?

This homework demonstrates your cumulative learning by showcasing how you have integrated prompt engineering, RAG, and tool-based interactions into a working AI system.

---

## ✅ Your Deliverable

### AI Agent System with RAG and Tools [100 pts]

Your deliverable should be a complete system that demonstrates:

- **Multi-Agent Orchestration:** a workflow with 2–3 agents working together (from LAB 1)
- **RAG Integration:** context-aware responses using retrieval from your data source (from LAB 2)
- **Function Calling:** agents that use tools to interact with external APIs or data sources (from LAB 3)

**Requirements:**

- [ ] **📝 [25 pts] Writing Component:** brief written explanation of your system (**NOT** AI-generated)
  - Explain what your system does
  - Describe how the components work together
  - Discuss any design choices or challenges you encountered
  - Written in your own words (3+ paragraphs)

- [ ] **🔗 [25 pts] Code, as Git Repository Links:** working, valid links to relevant content in your git repository
  - Link to your multi-agent orchestration script
  - Link to your RAG implementation
  - Link to your function calling / tool definitions
  - Link to your main system file (if different)
  - Links must be functional and point to the correct files  
  - *If you use the course `HW2/` example:* link to [`clinical_pipeline.py`](../HW2/clinical_pipeline.py), [`retrieval.py`](../HW2/retrieval.py), and [`functions.py`](../HW2/functions.py) (or your fork’s copies), plus one sample under `out/`.

- [ ] **📸 [25 pts] Screenshots/Outputs:** screenshots and/or samples of outputs
  - Screenshot showing your multi-agent workflow in action
  - Screenshot demonstrating RAG retrieval and response
  - Screenshot showing function calling / tool usage
  - At least 3–4 screenshots total  
  - *Suggestions from `HW2/`:* Shiny dashboard after a successful run; or terminal after `python clinical_pipeline.py`; `out/retrieval_verification.md` or `out/retrieval_payload.json`; `out/agent1_tool_trace.json` or the function-calling section in `out/agent1_cohort_findings.md`.

- [ ] **📚 [25 pts] Documentation:** brief documentation for your system
  - **System Architecture:** description of your agent roles and workflow
  - **RAG Data Source:** description of your data source and search function
  - **Tool Functions:** table or list describing each tool: name, purpose, parameters, and what it returns
  - **Technical Details:** any information needed to understand your software (e.g., API keys, endpoints, packages, file structure)
  - **Usage Instructions:** how to install dependencies, set up data sources, configure API keys, and run the system — **make it easy to reproduce**  
  - *You may point readers to [`HW2/README.md`](../HW2/README.md) for install/run and add a short paragraph explaining how your submission maps to that layout.*

**Total: 100 pts**

---

## 📤 To Submit

- For credit: submit all four required components listed in the **Requirements** section above (100 pts total). **Submit a single .docx file.**

Submit via Canvas by the date specified in the course schedule.

---

![](../../docs/images/homework.png)

---

← 🏠 [Back to Top](#HOMEWORK)
