from google.adk.agents import Agent
from app.config.model_config import MODEL_NAME
from app.tools.repository_scanner import scan_workspace
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters


filesystem_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="cmd",
            args=[
                "/c",
                "npx",
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "--read-only",
                r"C:\Users\barat\Documents\Google ADK AGents\SD_assistant\workspace",
            ],
        ),
        timeout=30,
    ),

    tool_filter=[
        "list_directory",
        "directory_tree",
        "read_text_file",
        "search_files",
    ],
)


repository_agent = Agent(
    name="repository_agent",
    model=MODEL_NAME,
    mode="single_turn",
    description="Inspects and analyzes software repositories.",
    instruction="""
    You are a Repository Analysis Agent.

    Follow this sequence:

    1. First call scan_workspace to obtain repository metadata.
    2. Identify the relevant files based on the user's request.
    3. Use filesystem MCP tools to inspect those files.
    4. Prepare a compact repository analysis.

    Return:
    - Repository name
    - Programming languages
    - Frameworks
    - Entry points
    - Important configuration files
    - Relevant files for the requested feature
    - Existing implementation related to the feature

    Rules:
    - Do not modify files.
    - Do not read every source file.
    - Do not read secrets or environment files.
    - Report only verified findings.
    - Keep the summary concise.
    """,
    tools=[
        scan_workspace,
        filesystem_toolset
    ],
    output_key="repository_summary"
)