from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import Tool
from tools.agent_tools import FileTools, FileInfo
from dotenv import load_dotenv
from enum import Enum
import os

load_dotenv()

def load_prompt(filename: str) -> str:
    """Loads a prompt from a file in the same directory as this script."""
    prompt_path = os.path.join(os.path.dirname(__file__), filename)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

class RequestType(Enum):
    INVALID = "invalid"
    SIMPLE = "simple"
    COMPLEX = "complex"

class RequestClassification(BaseModel):
    request_type: RequestType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class AgentState(BaseModel):
    base_dir: str
    last_action: Optional[str] = None
    last_result: Optional[str] = None

class MultiModelFileAgent:
    def __init__(self, base_dir: str, light_model: str, powerful_model: str):
        self.light_model = light_model
        self.powerful_model = powerful_model
        self.tools = FileTools(base_dir)
        self.state = AgentState(base_dir=base_dir)
        
        self.classifier = Agent(
            model=light_model,
            deps_type=AgentState,
            output_type=RequestClassification,
            system_prompt=load_prompt("classifier_prompt.txt")
        )
        
        self.main_agent = Agent(
            model=powerful_model,
            deps_type=AgentState,
            output_type=str,
            system_prompt=load_prompt("main_agent_prompt.txt")
        )
        
        self.simple_agent = Agent(
            model=light_model,
            deps_type=AgentState,
            output_type=str,
            system_prompt=load_prompt("simple_agent_prompt.txt")
        )
        
        self.register_tools(self.main_agent)
        self.register_tools(self.simple_agent)
    
    def register_tools(self, agent):
        @agent.tool_plain
        def list_files() -> List[Dict[str, Any]]:
            files = self.tools.list_files()
            print(f"Listing files:")
            print(files)
            
            self.state.last_action = "list_files"
            self.state.last_result = f"Found {len(files)} files"
            return [f.model_dump() for f in files]
            
        @agent.tool_plain
        def read_file(filename: str) -> str:
            """Read and return the content of a file."""
            content = self.tools.read_file(filename)
            print(f"Reading file: {filename}")
            
            self.state.last_action = f"read_file: {filename}"
            self.state.last_result = f"Read {len(content)} characters"
            return content
        
        @agent.tool_plain
        def write_file(filename: str, content: str, mode: str = 'w') -> str:
            """Write content to a file. Mode can be 'w' (overwrite) or 'a' (append)."""
            result = self.tools.write_file(filename, content, mode)
            print(f"Writing file: {filename}")
            
            self.state.last_action = f"write_file: {filename} (mode: {mode})"
            self.state.last_result = f"Wrote {len(content)} characters"
            return result
        
        @agent.tool_plain
        def delete_file(filename: str) -> str:
            result = self.tools.delete_file(filename)
            print(f"Deleting file: {filename}")
            self.state.last_action = f"delete_file: {filename}"
            self.state.last_result = "File deleted successfully"
            return result
        
        @agent.tool_plain
        def answer_question_about_files(query: str) -> str:
            result = self.tools.answer_question_about_files(query)
            print(f"Answering question about files: {query}")
            self.state.last_action = f"answer_question: {query[:50]}..."
            self.state.last_result = "Analyzed files and provided answer"
            return result
        
    
    async def classify_request(self, user_input: str) -> RequestClassification:
        try:
            result = await self.classifier.run(user_input, deps=self.state)
            return result.output
        except Exception as e:
            return RequestClassification(
                request_type=RequestType.COMPLEX,
                confidence=0.5,
                reasoning=f"Classification failed: {str(e)}, defaulting to complex analysis",
            )
    
    async def handle_invalid_request(self, classification: RequestClassification) -> str:
        if "unrelated" in classification.reasoning.lower():
            return "I'm a file management assistant. I can help you with file operations like reading, writing, listing, and analyzing files in your directory. Please ask me something related to file management."
        
        else:
            return f"I couldn't understand your request. {classification.reasoning} Please rephrase your question more clearly, focusing on what you'd like to do with files."
    
    async def handle_simple_request(self, user_input: str) -> str:
        try: 
            result = await self.simple_agent.run(user_input, deps=self.state)
            return result.output
        except Exception as e:
            return f"Error handling simple request: {str(e)}"
    
    async def handle_complex_request(self, user_input: str) -> str:
        try:
            result = await self.main_agent.run(user_input, deps=self.state)
            return result.output
        except Exception as e:
            return f"Error handling complex request: {str(e)}"
    
    async def process(self, user_input: str) -> str:
        try:
            classification = await self.classify_request(user_input)
            
            if classification.request_type == RequestType.INVALID:
                response = await self.handle_invalid_request(classification)
                
            elif classification.request_type == RequestType.SIMPLE:
                print("Using simple agent...")
                response = await self.handle_simple_request(user_input)
                    
            else:
                print("Using complex agent...")
                response = await self.handle_complex_request(user_input)
    
            return response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.state.last_result = error_msg
            return error_msg
