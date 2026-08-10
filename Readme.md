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

The crewai framework's native tool-call representation is logged in the agents_outputs.json file. The log includes the resolved tool name and parsed arguments for each tool call made by the agents.



4.	Demonstrate the full loop on at least three distinct user queries or tasks , each exercising at least one of your tools. For each, record in the README: the query/task, which tool(s) were called with which arguments, and the final answer produced.
Option B — CrewAI multi-agent crew
1.	Define at least two agents, each with a distinct role, goal, and backstory reflecting a specialised skill (e.g., an investigator agent that gathers facts via tools, and a writer agent that drafts output from those facts).
2.	Define at least two Task objects (description + expected_output), each assigned to one agent, where at least one task's output is explicitly passed as context/input to a later task (a task handoff).
3.	Assemble a Crew and run it once using Process.sequential. Then run the same or an extended crew a second time using Process.hierarchical with a manager agent that delegates to your specialist agents. In the README, briefly compare what differed between the sequential run and the hierarchical run (who decided the task order, and whether the outputs differed).
4.	Set allow_delegation=True on at least one agent, and in the README either show a concrete example where that agent used delegation to get help from a teammate midtask, or explain clearly why delegation was not triggered in your run.
Acceptance criteria (your submission is complete when…)
●	At least two tools exist, at least one calling a real external API; each is documented in the README's tool-contract table with a read/write label.
●	For every demonstrated tool call, the resolved {tool, arguments} decision is extracted from the framework's own native tool-calling mechanism (not hand-parsed from raw text) and a real logged example is shown in the README.
●	The end-to-end loop is demonstrated on at least three distinct queries/tasks with tool calls, arguments, and final answers all recorded in the README.
●	Option A: the agent is built with @tool-decorated functions, a tool-calling agent + AgentExecutor with bounded max_iterations; a 2-turn memory demonstration shows correct reuse of turn-1 information in turn 2; a separate
o	RunnablePassthrough/RunnableBranch conditional workflow is implemented and its two possible routes are both shown running (e.g., by invoking it twice with inputs that trigger each branch).
●	Option B: at least two agents (role/goal/backstory) and at least two tasks (with one handoff) are defined; both a sequential run and a hierarchical run (with a manager agent) are executed and compared in the README; at least one agent has allow_delegation=True, with the delegation outcome documented.
●	No API key appears anywhere in the repository; required environment-variable names are documented in the README.
Submission
Submit one public GitHub repository link. The repository must contain the agent implementation, all tool definitions, a recorded trace of your end-to-end demonstration runs, and a README.md covering every point in the acceptance criteria (including which option you chose and why).

