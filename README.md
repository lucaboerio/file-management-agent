# Multi-Model File Management Agent

An intelligent file management system that uses multiple AI models to optimize performance and costs. 
The system automatically classifies requests and uses the most appropriate model for each operation.

## Features

- **Intelligent Routing**: Automatically classifies requests as simple, complex, or invalid
- **Multi-Model Architecture**: Uses lightweight models for simple operations and powerful models for complex analysis
- **Multiple Interfaces**: Interactive CLI, single commands, and MCP server
- **Complete File Management**: Reading, writing, deletion, analysis, and search
- **Context Awareness**: Maintains context from previous conversations (for Interactive CLI)

## Requirements

- Python 3.8+
- OpenAI API Key
- Libraries listed in `requirements.txt`

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd file-management-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   LIGHT_MODEL=openai:gpt-3.5-turbo
   POWERFUL_MODEL=openai:gpt-4o
   WORK_DIR=you_preferred_path #or leave blanck and use default directory
   ```

## Usage

### 1. Interactive CLI Interface

Start an interactive chat session:

```bash
python cli_interface/cli_chat.py
```

Usage example:
```
> create a file named hello.txt with content "Hello World"
--> File 'hello.txt' created successfully

> what files are in the directory?
--> Files in directory:
- hello.txt (11 bytes)

> analyze all text files and tell me their content
--> [Detailed content analysis...]
```

### 2. Single Command

Execute a single command:

```bash
python cli_interface/cli_agent.py "list all files" --verbose
```

Available options:
- `--dir`: Working directory (default: ./file_workspace)
- `--light-model`: Model for simple operations
- `--powerful-model`: Model for complex operations
- `--verbose, -v`: Detailed output

### 3. MCP Server (Model Context Protocol)

In order to see the server running correctly:

```bash
python mcp_server.py
```

Configure `mcp_config.json` with your paths and credentials.

## How It Works

### Intelligent Classification

The system automatically classifies each request:

- **SIMPLE**: Basic operations like listing files, reading single files
- **COMPLEX**: Multi-file analysis, pattern recognition, complex operations
- **INVALID**: Unrelated or malformed requests

### Classification Examples

**Simple Requests:**
- "What files are here?"
- "Show me the directory contents"
- "Read file example.txt"

**Complex Requests:**
- "Analyze all Python files and find common patterns"
- "Compare the content of all text files"
- "Create a summary of all documentation files"

**Invalid Requests:**
- "What's the weather today?"
- "Tell me a joke"

### Available Tools

- `list_files()`: Lists all files in the directory
- `read_file(filename)`: Reads the content of a file
- `write_file(filename, content, mode)`: Writes or appends content
- `delete_file(filename)`: Deletes a file
- `answer_question_about_files(query)`: Analyzes files to answer questions

## 📁 Project Structure

```
├── agent/
│   ├── agent.py                 # Main agent with state management
│   ├── classifier_prompt.txt    # Classification prompt
│   ├── main_agent_prompt.txt    # Complex operations prompt
│   └── simple_agent_prompt.txt  # Simple operations prompt
├── cli_interface/
│   ├── cli_agent.py            # CLI interface for single commands
│   └── cli_chat.py             # Interactive CLI interface
├── tools/
│   └── agent_tools.py          # File management tools
├── mcp_server.py               # MCP server for integrations
├── mic_config.json             # MCP configuration
└── requirements.txt            # Python dependencies
```
