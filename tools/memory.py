from tools.registry import registry
from core.jarvis import jarvis

@registry.register(
    name="remember",
    description="Store an important fact, preference, or snippet in the permanent Memory Palace.",
    params={
        "content": "The actual information to remember",
        "title": "A short descriptive title",
        "tags": "Optional list of tags e.g. ['user', 'preferences']"
    }
)
def remember(content: str, title: str = "", tags: list[str] = None):
    item_id = jarvis.memory.remember(content, title=title, tags=tags)
    return f"Information stored in Memory Palace with ID: {item_id}"

@registry.register(
    name="forget",
    description="Remove an item from the Memory Palace by its ID.",
    params={"item_id": "The ID of the memory item to delete"}
)
def forget(item_id: str):
    jarvis.memory.forget(item_id)
    return f"Memory item {item_id} has been forgotten."

@registry.register(
    name="search_memory",
    description="Search the Memory Palace for specific information.",
    params={"query": "Search query keywords"}
)
def search_memory(query: str):
    results = jarvis.memory.recall(query)
    if not results:
        return "No matching memories found."
    
    summary = ["Matching memories:"]
    for r in results:
        summary.append(f"- [{r['id']}] {r['title']}: {r['content']}")
    return "\n".join(summary)
