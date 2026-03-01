# HW1 Pipeline – Process Diagram with Stakeholder Needs

Copy the code below and paste it into [Mermaid Live Editor](https://mermaid.live). Paste only the lines inside the code block (from `flowchart TB` down to the last line); the site expects raw Mermaid, so omit the surrounding triple-backtick fences.

```mermaid
flowchart TB
  Setup[Setup and env check]
  Fetch[Socrata fetch]
  Clean[Clean and coerce]
  Agg[Aggregate by year]
  Model[Fit Poisson model]
  JSON[Build results JSON]
  SaveJson[Save HW1_results.json]
  Ollama[Ollama report]
  SaveReport[Save HW1_report.md]

  Setup --> Fetch --> Clean --> Agg --> Model --> JSON --> SaveJson --> Ollama --> SaveReport

  subgraph stakeholder_needs [Stakeholder needs]
    Analyst[Analyst: Reproducible pipeline and interpretable model]
    CDC[CDC: Correct use of data and SoQL]
    Reader[Reader: Clear report with caveats]
    Operator[Operator: Env vars and error handling]
  end

  Analyst -.->|addressed by| Model
  Analyst -.->|addressed by| SaveJson
  CDC -.->|addressed by| Fetch
  Reader -.->|addressed by| Ollama
  Reader -.->|addressed by| SaveReport
  Operator -.->|addressed by| Setup
```
