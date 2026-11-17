from .agent import get_campus_resource_info  # Imports directly from agent.py

def test_library_lookup():
    result = get_campus_resource_info("library")
    assert result.get("status") == "success"
    assert result.get("data", {}).get("name") == "Library"

def test_tutoring_alias():
    result = get_campus_resource_info("tutoring")
    assert result.get("status") == "success"
    assert result.get("data", {}).get("name") == "Tutoring Center"

def test_case_insensitive():
    result = get_campus_resource_info("LIBRARY")
    assert result.get("status") == "success"
    assert result.get("data", {}).get("name") == "Library"

def test_resource_not_found():
    result = get_campus_resource_info("dental office")
    assert result.get("status") == "error"
    assert "Available resources" in result.get("error_message", "")

def test_list_all_resources():
    result = get_campus_resource_info("all")
    assert result.get("status") == "success"
    assert "available_resources" in result
    assert len(result["available_resources"]) >= 4