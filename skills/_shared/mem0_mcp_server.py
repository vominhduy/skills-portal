#!/usr/bin/env python3
"""
Mem0 Shared Long-Term Memory MCP Server
Provides MCP tools for Antigravity CLI and external agents:
- mem0_search_memory
- mem0_add_memory
- mem0_list_memories
- mem0_delete_memory
"""
import sys
import json
import os

# Add current dir to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mem0_service

TOOLS = [
    {
        "name": "mem0_search_memory",
        "description": "Search for relevant shared long-term memories across Project Context, User Preferences, and Decisions History.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for memories"
                },
                "category": {
                    "type": "string",
                    "enum": ["project_context", "user_preference", "decisions_history"],
                    "description": "Optional category filter"
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of memories to return"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "mem0_add_memory",
        "description": "Save an important project fact, user preference, or technical decision into shared long-term memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The exact fact, decision, or preference to remember"
                },
                "category": {
                    "type": "string",
                    "enum": ["project_context", "user_preference", "decisions_history"],
                    "description": "Category for the memory"
                },
                "user_id": {
                    "type": "string",
                    "default": "global",
                    "description": "User identifier"
                },
                "project_id": {
                    "type": "string",
                    "default": "default",
                    "description": "Project identifier"
                }
            },
            "required": ["content", "category"]
        }
    },
    {
        "name": "mem0_list_memories",
        "description": "List all shared long-term memories in a given category.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["project_context", "user_preference", "decisions_history"],
                    "description": "Optional category filter"
                }
            }
        }
    },
    {
        "name": "mem0_delete_memory",
        "description": "Delete a memory item from shared long-term memory by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "The ID of the memory to delete"
                }
            },
            "required": ["memory_id"]
        }
    }
]

def handle_call_tool(name: str, args: dict):
    if name == "mem0_search_memory":
        query = args.get("query", "")
        category = args.get("category")
        limit = int(args.get("limit", 5))
        results = mem0_service.search_memories(query=query, category=category, limit=limit)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, ensure_ascii=False, indent=2)
                }
            ]
        }
    elif name == "mem0_add_memory":
        content = args.get("content", "")
        category = args.get("category", "project_context")
        user_id = args.get("user_id", "global")
        project_id = args.get("project_id", "default")
        result = mem0_service.add_memory(content=content, category=category, user_id=user_id, project_id=project_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ]
        }
    elif name == "mem0_list_memories":
        category = args.get("category")
        results = mem0_service.list_memories(category=category)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(results, ensure_ascii=False, indent=2)
                }
            ]
        }
    elif name == "mem0_delete_memory":
        mem_id = args.get("memory_id", "")
        ok = mem0_service.delete_memory(mem_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"ok": ok, "id": mem_id}, ensure_ascii=False)
                }
            ]
        }
    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "mem0-shared-memory",
                            "version": "1.0.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            elif method == "tools/call":
                params = req.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = handle_call_tool(tool_name, tool_args)
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            elif method == "ping":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            else:
                # ignore other notifications
                if req_id is not None:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
        except Exception as e:
            if 'req_id' in locals() and req_id is not None:
                err_res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()

if __name__ == '__main__':
    main()
