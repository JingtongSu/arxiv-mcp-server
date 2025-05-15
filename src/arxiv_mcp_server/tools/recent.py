"""Recent papers functionality for the arXiv MCP server."""

import arxiv
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from dateutil import parser
import mcp.types as types
from ..config import Settings
from .search import _process_paper  # Reusing the paper processing function

settings = Settings()

recent_tool = types.Tool(
    name="recent_papers",
    description="Get the most recent papers from specified arXiv categories",
    inputSchema={
        "type": "object",
        "properties": {
            "categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of arXiv categories (e.g., ['cs.AI', 'cs.LG'])"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of papers to return"
            }
        },
        "required": ["categories"],
    },
)

async def handle_recent(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle recent papers requests."""
    try:
        client = arxiv.Client()
        max_results = min(int(arguments.get("max_results", 10)), settings.MAX_RESULTS)
        categories = arguments["categories"]

        # Build category filter query
        category_filter = " OR ".join(f"cat:{cat}" for cat in categories)
        
        # Create search with category filter
        search = arxiv.Search(
            query=category_filter,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        # Process results
        results = []
        for paper in client.results(search):
            results.append(_process_paper(paper))
            if len(results) >= max_results:
                break

        response_data = {
            "total_results": len(results),
            "categories": categories,
            "papers": results
        }

        return [
            types.TextContent(type="text", text=json.dumps(response_data, indent=2))
        ]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]