import json
from pathlib import Path
from google.adk.agents import Agent

RESOURCE_FILE = Path(__file__).parent / "campus_resources.json"

def get_campus_resource_info(resource_name: str) -> dict:
    """Use this tool whenever someone asks about a campus service, location, hours, or contact information.

    Args:
        resource_name: The name or alias of the campus resource (e.g., 'library', 'advising', 'helpdesk').

    Returns:
        dict: Information about the requested campus resource or an error message if not found.
    """
    try:
        with open(RESOURCE_FILE, "r", encoding="utf-8") as f:
            resources = json.load(f)
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to load resource data: {str(e)}"}

    resource_name_clean = resource_name.lower().strip()

    for item in resources:
        name_match = resource_name_clean in item.get("name", "").lower()
        alias_match = any(resource_name_clean in alias.lower() for alias in item.get("aliases", []))
        
        if name_match or alias_match:
            return {"status": "success", "data": item}

    available_names = [r.get("name") for r in resources if "name" in r]
    return {
        "status": "error",
        "error_message": f"No information was found for '{resource_name}'. Available resources: {available_names}."
    }

root_agent = Agent(
    model="gemini-3.8-flash",
    name="campus_resource_agent",
    description="Answers questions about college campus resources.",
    instruction=(
        "You are the Campus Resource Assistant. Answer questions accurately using only "
        "the provided tool. If the tool returns status 'error', do not invent information."
    ),
    tools=[get_campus_resource_info],
)