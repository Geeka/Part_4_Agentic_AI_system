# Part 4 — Agentic AI System: Tool-Using Agent with CrewAI 

## GOAL: Build a multi agent job search crewai system that 
- reads a local resume, extracts relevant information and derives a search query
- searches for jobs using a free job search API and selects one most relevant job from 5 outputs obtained   , and
- sends email to the user with the selected job and a reason for selection, along with 5 job listings with an apply link for each job listing. The email also includes a draft resume and cover letter for the selected job.

- drafts resume and cover letter for the selected job (the final output is sent to the user via email using deterministic templates)

The final output is sent to the user via email using deterministic templates.

## Environment variables:
 The following variables are obtained from env file

OPENAI_API_KEY="your_openai_api_key"
OPENROUTER_API_KEY="your_openrouter_api_key"
SERPAPI_API_KEY="your_serpapi_api_key"

EMAIL_SMTP_SERVER="smtp.gmail.com"
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS="your_email_address"
EMAIL_PASSWORD="your_email_app_password"
The app password is not the gmail password, but a special password generated for use with apps. See https://support.google.com/accounts/answer/185833?hl=en for more information.

External API used:
SerpAPI Job search tool: https://serpapi.com/jobs-api


## Tools defined: 

** Get_resume_tool: **
A tool that reads a local resume file and extracts relevant information such as skills, experience, and education.

** Job_search_tool: **
A tool that takes a job title and location as input and returns a list of job postings from a free job search API.
This uses the SerpAPI API call: https://serpapi.com/jobs-api through the function call_api function within tools.py



2.	Design every tool to the four taught good-tool properties — Clear name, Honest/accurate description, Atomic (does one job), Safe (returns errors as data, never crashes the agent) — and document each tool in the README as a short tool-contract table: name, one-line description, parameters, and whether it is a read tool (fetches data only) or a write tool (would change state — flag if any of your tools are write tools and what safeguard you added).

| Tool | Description | Parameters | Type | Notes |
|---|---|---|---|---|
| Job Search | Searches for 5 real, current job postings (last 7 days) matching the query. Returns a JSON list of jobs with title, company, location, description, apply_link. Pure read -- no side effects. | `query: str` | Read | Catches exceptions internally and returns `{"error": "..."}` instead of raising -- never crashes agent execution. |
| Get Resume | Returns the candidate's full, exact resume text. Takes no arguments. | none | Read | Resume is loaded and validated once at startup (`load_resume()`), before any agent runs, so this call cannot fail mid-session. |


3.	Document how your framework communicates the tool-selection decision as a {tool, arguments} contract. Both
create_tool_calling_agent/AgentExecutor (Option A) and CrewAI's agent runtime (Option B) already parse the model's tool choice into a structured object internally — do not hand-write a raw-text JSON regex parser on top of a framework that already does this. Instead, for every tool call your agent makes: (a) inspect your framework's native tool-call representation (e.g., LangChain's intermediate steps /
tool_calls, or CrewAI's tool-usage log) and extract the resolved tool name and parsed arguments from it; (b) print/log that as an explicit {"tool": ...,
"arguments": {...}} object at the moment of each call; (c) include at least one real captured example of this logged object per demonstrated query in the README, as evidence that the routing decision is structured and inspectable.

The crewai framework's native tool-call representation is logged in the agents_outputs.json file. The log includes the resolved tool name and parsed arguments for each tool call made by the agents. the sample log taken from software_engineer_output.txt is as follows:


```
[TOOL CALL] {"tool": "job_search", "arguments": {"query": "junior backend engineer"}, "agent_role": "Manager Agent"}
Tool job_search executed with result: [{"title": "Junior .NET Backend Engineer \u2014 Remote-Ready", "company": "Metrc LLC", "location": "United States", "description": "Metrc LLC is seeking a motivated Backend .NET Engineer to support sc...
[Finalize] todos_count=0, todos_with_results=0
```

## Outputs for 3 different resumes   

The output of the entire crew process successfully ran with 3 different resumes

Entry level data analyst resume and output
[resume.txt](resume.txt)

Output of the entire crew process successfully ran with the entry level data analyst resume
[output.txt](output.txt)

Marketing Analyst Resume and Output
[resume_marketing_analyst.txt](resume_marketing_analyst.txt)

Output of the entire crew process successfully ran with the marketing analyst resume
[marketing_analyst_output.txt](marketing_analyst_output.txt)


Software Engineer Resume and Output
[resume_software_engineer.txt](resume_software_engineer.txt)

Output of the entire crew process successfully ran with the software engineer resume
[software_engineer_output.txt](software_engineer_output.txt)

The entire run outputs are stored in the corresponding output files.


4.	Demonstrate the full loop on at least three distinct user queries or tasks , each exercising at least one of your tools. For each, record in the README: the query/task, which tool(s) were called with which arguments, and the final answer produced.


The hierarchical and sequential run are done in the same run

allow_delegation=true is allotted to manager agent

## Sequential vs. Hierarchical — Observed Comparison

**Task routing / delegation**
- Sequential: tasks always execute in the fixed order defined (analyze_resume_task -> search_task), with each agent doing exactly its assigned task. No routing decision involved.
- Hierarchical: in every run observed, jobs_manager did not delegate to resume_analyst/search_agent as separate actors -- it called get_resume and job_search directly itself, appearing in logs as "agent_role": "Manager Agent". Despite allow_delegation=True, no delegate_work_to_coworker call appeared in the two-agent runs -- the manager simply executed the work in-role rather than routing it out.

**Tool-call reliability**
- Sequential run (marketing analyst query): the Search Agent hallucinated a nonexistent tool name (job_search_channel_commentary) partway through, and its final answer discarded all search results, returning an empty search_results: [] despite two legitimate job_search calls having fired.
- Hierarchical runs (data scientist queries): no hallucinated tool names observed in any hierarchical run; tool calls stayed to get_resume and job_search only.
- Based on available data, hierarchical mode showed no repeat instances of this specific hallucination failure, while sequential did -- though sample size is small (one clear instance) and this may not generalize.

**Number of search calls per run**
- Sequential: ranged from 1 call up to 4 calls in a single task execution (e.g. "entry-level data scientist", then 3 geography-variant retries), driven entirely by the agent's own judgment since no call-count instruction is given.
- Hierarchical: consistently 1 call per run across every hierarchical log observed ("junior data scientist" once, no retries or variant queries).
- Hierarchical was more token/cost-efficient on search calls in every run observed; sequential's agent showed more variable, sometimes redundant search behavior.

**Job selection quality / spam filtering**
- Sequential run results included multiple SynergisticIT/staffing-mill spam listings selected as the "best fit," with the agent's own stated reasoning factually inconsistent with the listing it picked (claimed it was "the only posting that explicitly mentions a data scientist role" while the listing itself was generic staffing-mill copy).
- Hierarchical run selected Eliassen Group -- a substantive listing with concrete requirements -- over the same SynergisticIT postings that appeared in its own search results, correctly avoiding the spam pick that sequential mode selected in a comparable run.
- In the runs observed, hierarchical mode produced better spam-filtering outcomes than sequential -- but again only one

