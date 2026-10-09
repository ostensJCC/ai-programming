import json
from pathlib import Path
from google.adk import Agent

RESOURCE_FILE = Path(__file__).parent / "campus_resources.json"


def get_campus_resource_info(resource_name: str) -> dict:
    """Use this tool whenever someone asks about a campus service, location, 
    hours, contact details, or available resources.

    Args:
        resource_name: The name or alias of the campus resource (e.g., 'library', 'advising').

    Returns:
        dict: Information about the requested resource or an error status if not found.
    """
    if not RESOURCE_FILE.exists():
        return {"status": "error", "error_message": "Resource data file missing."}

    with open(RESOURCE_FILE, "r", encoding="utf-8") as f:
        resources = json.load(f)

    query = resource_name.strip().lower()

    for item in resources:
        name_match = query in item.get("name", "").lower()
        alias_match = any(query in alias.lower() for alias in item.get("aliases", []))
        if name_match or alias_match:
            return {"status": "success", "data": item}

    available = [item.get("name") for item in resources if "name" in item]
    return {
        "status": "error",
        "error_message": (
            f"No information was found for '{resource_name}'. "
            f"Available resources: {available}."
        ),
    }


root_agent = Agent(
    model="gemini-flash-latest",
    name="campus_resource_agent",
    description="Answers questions about college campus resources.",
    instruction=(
        "You are the Campus Resource Assistant. Answer questions about campus services, "
        "locations, hours, and contact information. Always use the get_campus_resource_info "
        "tool to look up information before answering. If the tool returns an error status, "
        "politely inform the user and state which resources are available without inventing details."
    ),
    tools=[get_campus_resource_info],
)