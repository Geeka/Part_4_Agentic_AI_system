
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
import pprint
load_dotenv()
from tools import (
    call_api,
    extract_job_fields,
    render_email_body,
    send_email,
)

os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

llm = LLM(
    model="openai/gpt-oss-20b",
    provider="openrouter",
    temperature=0.4,
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# ---------- INPUT ----------
BASE_DIR = Path(__file__).parent
RESUME_PATH = BASE_DIR / "resume.txt"
CANDIDATE_EMAIL = "candidate@example.com"

def process_final_output(final_raw, manager=False):
    print()
    print("-------------------------------------------------")
    print("-------------------Output Summary----------------")
    print("-------------------------------------------------")
    profile = json.loads(str(analyze_resume_task.output))
    search_output = json.loads(str(search_task.output)) if search_task.output else {}

    all_jobs = search_output.get("search_results", [])
    selected_job = search_output.get("selected_job", {})
    reason_selected = search_output.get("reason_selected", "")
    with open(BASE_DIR / "agents_outputs.json", "a", encoding="utf-8") as f:
        f.write("----------Resume Analyst output ----------")
        f.write(json.dumps({"resume_analyst_output": str(analyze_resume_task.output)}, indent=2))
        f.write("\n\n")

        f.write("----------Search Analyst output ----------")
        f.write(json.dumps({"search_analyst_output": str(search_task.output)}, indent=2))
        f.write("\n\n")
        

    print("----------Resume Analyst output ----------")
    pprint.pprint(str(analyze_resume_task.output))
    print("\n===== CANDIDATE =====")
    print(profile.get("name", "(no name returned)"))
    print("\n===== CANDIDATE SUMMARY =====")
    print(profile.get("summary", "(no summary returned)"))
    print("\n===== DERIVED SEARCH QUERY =====")
    print(profile.get("search_query", "(no query returned)"))
    print("\n===== SEARCH AGENT'S SELECTED JOB =====")
    pprint.pprint(str(search_task.output))
    if not all_jobs:
        print("\nNo jobs found for this query. Nothing to send.")
        raise SystemExit(0)

    email_payload = {
        "jobs": all_jobs,
        "top_pick": selected_job,
        "why_this_one": reason_selected,
    }  
    # Final processing step -- plain, deterministic, never delegated to any agent.
    body = render_email_body(email_payload)
    outcome = send_email(CANDIDATE_EMAIL, "Your Matched Jobs This Week", body)

    filename=BASE_DIR / "output_hierarchical.md" if manager else BASE_DIR / "output_sequential.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Summary: {profile.get('summary', '')}\n")
        f.write(f"Search query: {profile.get('search_query', '')}\n\n")
        f.write(f"\n\n{outcome}\n")

    print("\n===== 5 JOBS FOUND =====")
    print(json.dumps(all_jobs, indent=2))
    print(f"\n{outcome}")


# Loads resume into memory once at startup, so all agents see the same content and
def load_resume() -> str:
    if not RESUME_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {RESUME_PATH}. Create resume.txt with your resume text."
        )
    text = RESUME_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("resume.txt is empty. Paste your resume content into it.")
    return text


resume = load_resume()


# ---------- TOOL 1: on the Search Agent -- always called, gets real data ----------

@tool("Job Search")
def job_search_tool(query: str) -> str:
    """Searches for 5 real, current job postings (last 7 days) matching the query. Returns a JSON list of jobs with title, company, location, description, apply_link. Pure read -- has no side effects."""
    try:
        raw = call_api(query, num_results=5)
        jobs = [extract_job_fields(r) for r in raw]
    except Exception as e:
        return json.dumps({"error": f"Job search failed: {e}"})
    return json.dumps(jobs)

# ---------- TOOL 2: on Resume Analyst + Apply Agent -- always called, gets the real resume ----------
# Returns the full, real resume text on demand rather than embedding it
# directly in a task description string. A tool call's result appears
# once in the log as a compact block; an embedded f-string gets reprinted
# every time CrewAI logs the task, which is what caused earlier
# duplication. Search Agent does not get this tool -- it only needs the
# profile summary (passed via context), not the raw resume.
#
# 
@tool("Get Resume")
def get_resume_tool() -> str:
    """Returns the candidate's full, exact resume text. Takes no arguments. Call this before drafting the cover letter or ATS resume so every detail (dates, project names, company names) is accurate rather than guessed."""
    return resume

# ---------- THE THREE AGENTS ----------

resume_analyst = Agent(
    role="Resume Analyst",
    goal="Extract a structured profile from the resume, including a realistic job search query",
    backstory=(
        "An expert technical recruiter who reads resumes carefully and "
        "reports only what's actually demonstrated -- skills, experience "
        "level, and a search query pitched at the candidate's real "
        "seniority, never inflated. Always calls the Get Resume tool "
        "first to read the real resume before answering."
    ),
    tools=[get_resume_tool],
    llm=llm, verbose=True,
)

search_agent = Agent(
    role="Search Agent",
    goal="Search for real job postings and select the single best-fit job by judgement",
    backstory=(
        "A discerning recruiter who searches real job boards and picks "
        "the one posting genuinely worth applying to -- not just the "
        "first or the most keyword-dense -- by weighing a candidate's "
        "real profile against each posting's real requirements. Never "
        "invents a posting; only selects from what the Job Search tool "
        "actually returned."
    ),
    tools=[job_search_tool],
    llm=llm, verbose=False,
)
jobs_manager= Agent(
    role="Manager Agent",
    goal="Oversee the Resume Analyst, Search Agent, and Apply Agent to ensure the process runs smoothly and the final output is accurate.",
    backstory=(
        "A senior recruiter who supervises the entire job application process. "
        "Ensures that each agent performs their tasks correctly and that the final output meets the candidate's needs."
    ),
    tools=[],allow_delegation=True,
    llm=llm, verbose=True,
)


# ---------- STEP 1: resume -> profile (LLM + tool) ----------
analyze_resume_task = Task(
    description=(
        "Read the resume and extract the candidate's "
        "skills, experience level, and seniority. Derive a realistic job "
        "search query matching their actual level (e.g. 'junior data "
        "analyst', not 'senior data scientist').\n\n"
        "Return ONLY JSON in this exact shape, no extra text:\n"
        '"search_query": "...", '
        '"summary": "1-2 sentence honest summary of the candidate"}'
        "Also pass the candidates actual resume text to the next task via context"
    ),
    
    expected_output=(
        "A single JSON object with the candidate profile: name, skills, "
        "experience_months, seniority, search_query, summary."
    ),
    agent=resume_analyst,
)

# ---------- STEP 2: search + select one job by judgement (LLM + tool) ----------
search_task = Task(
    description=(
        "Search for real, current job postings matching the query from the "
        "analyst. Check for hiring spam -- watch for generic staffing-mill "
        "listings, repeated marketing copy, vague or missing requirements, "
        "and postings that don't name a real hiring company. Then use your "
        "judgement to pick the ONE job which best fits the candidate's "
        "actual skills and experience level."
    ),
    expected_output=(
        'A single JSON object in this exact shape, no extra text: '
        '{"search_results": [ ...every job returned by your search, unchanged... ], '
        '"selected_job": { ...the one job you picked, including its exact apply_link... }, '
        '"reason_selected": "1 sentence on why this job was the best fit"}'
    ),
    agent=search_agent,
    context=[analyze_resume_task],
)

from crewai.events import crewai_event_bus
from crewai.events.types.tool_usage_events import ToolUsageStartedEvent
""" @crewai_event_bus.on(ToolUsageStartedEvent)
def diagnostic_listener(source, event):
    print(f"[DIAGNOSTIC] event type: {type(event).__name__}")
    print(f"[DIAGNOSTIC] available attrs: {[a for a in dir(event) if not a.startswith('_')]}")
    print(f"[DIAGNOSTIC] raw repr: {event}")
 """

tool_call_log = []

@crewai_event_bus.on(ToolUsageStartedEvent)
def log_tool_call(source, event):
    """Fires on CrewAI's native ToolUsageStartedEvent -- the framework's own
    parsed {tool, arguments} representation. Not a regex over printed text;
    this is the structured object CrewAI already builds internally when it
    resolves the model's tool choice."""
    call = {
        "tool": event.tool_name,
        "arguments": event.tool_args,
        "agent_role": event.agent_role,
    }
    tool_call_log.append(call)
    print(f"[TOOL CALL] {json.dumps(call)}")


# ---------- SEQUENTIAL CREW ----------

print("------------------------------------------------")
print("-------------------------------------------------")
print("-------------- SEQUENTIAL CREW ---------------")
print("------------------------------------------------")
print("------------------------------------------------")


crew_sequential = Crew(
    agents=[resume_analyst, search_agent],
    tasks=[analyze_resume_task, search_task],
    process=Process.sequential,
    verbose=False,
)

final_raw = crew_sequential.kickoff()
process_final_output(final_raw)


# ---------- HIERARCHICAL CREW ----------


print("------------------------------------------------")
print("-------------------------------------------------")
print("-------------- HIERARCHICAL CREW ---------------")
print("------------------------------------------------")
print("------------------------------------------------")
  

crew_hierarchical = Crew(
    agents=[resume_analyst, search_agent],
    tasks=[analyze_resume_task, search_task],
    process=Process.hierarchical,
    manager_agent=jobs_manager,
    verbose=False,
)
final_raw = crew_hierarchical.kickoff()
process_final_output(final_raw,True)
