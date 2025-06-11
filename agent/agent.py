from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import Tool
from tools.agent_tools import FileTools, FileInfo
import json
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
    last_classification: Optional[RequestClassification] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

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
        
        self.main_prompt_template = load_prompt("main_agent_prompt.txt") + """

Previous conversation context:
- Last action: {last_action}
- Last result: {last_result}
- Recent history: {conversation_history}

Use this context to provide continuity in your responses and reference previous actions when relevant."""

        self.simple_prompt_template = load_prompt("simple_agent_prompt.txt") + """

Previous conversation context:
- Last action: {last_action}
- Last result: {last_result}
- Recent history: {conversation_history}

Use this context to provide continuity in your responses."""
        
        self.main_agent = Agent(
            model=powerful_model,
            deps_type=AgentState,
            output_type=str,
            system_prompt=self.main_prompt_template.format(
                last_action="None", last_result="None", conversation_history="None"
            )
        )
        
        self.simple_agent = Agent(
            model=light_model,
            deps_type=AgentState,
            output_type=str,
            system_prompt=self.simple_prompt_template.format(
                last_action="None", last_result="None", conversation_history="None"
            )
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
            """Delete a file from the directory."""
            result = self.tools.delete_file(filename)
            print(f"Deleting file: {filename}")
            self.state.last_action = f"delete_file: {filename}"
            self.state.last_result = "File deleted successfully"
            return result
        
        @agent.tool_plain
        def answer_question_about_files(query: str) -> str:
            """Answer questions about files by analyzing the directory contents."""
            result = self.tools.answer_question_about_files(query)
            print(f"Answering question about files: {query}")
            self.state.last_action = f"answer_question: {query[:50]}..."
            self.state.last_result = "Analyzed files and provided answer"
            return result
        
    def get_context_for_prompt(self) -> Dict[str, str]:
        """Genera il contesto per i prompt degli agenti."""
        return {
            "last_action": self.state.last_action or "None",
            "last_result": self.state.last_result or "None",
            "conversation_history": str(self.state.conversation_history[-3:]) if self.state.conversation_history else "None"
        }
    
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
            context = self.get_context_for_prompt()
            updated_prompt = self.simple_prompt_template.format(**context)
            
            temp_agent = Agent(
                model=self.light_model,
                deps_type=AgentState,
                output_type=str,
                system_prompt=updated_prompt
            )
            self.register_tools(temp_agent)
            
            result = await temp_agent.run(user_input, deps=self.state)
            return result.output
        except Exception as e:
            return f"Error handling simple request: {str(e)}"
    
    async def handle_complex_request(self, user_input: str) -> str:
        try:
            context = self.get_context_for_prompt()
            updated_prompt = self.main_prompt_template.format(**context)
            
            temp_agent = Agent(
                model=self.powerful_model,
                deps_type=AgentState,
                output_type=str,
                system_prompt=updated_prompt
            )
            self.register_tools(temp_agent)
            
            result = await temp_agent.run(user_input, deps=self.state)
            return result.output
        except Exception as e:
            return f"Error handling complex request: {str(e)}"
    
    async def process(self, user_input: str) -> str:
        try:
            classification = await self.classify_request(user_input)
            self.state.last_classification = classification
            
            if classification.request_type == RequestType.INVALID:
                response = await self.handle_invalid_request(classification)
                
            elif classification.request_type == RequestType.SIMPLE:
                print("Using simple agent...")
                response = await self.handle_simple_request(user_input)
                    
            else:
                print("Using complex agent...")
                response = await self.handle_complex_request(user_input)
        
            self.state.conversation_history.append({
                "user_input": user_input,
                "response": response,
                "classification": classification.request_type.value
            })
            
            if len(self.state.conversation_history) > 10:
                self.state.conversation_history = self.state.conversation_history[-10:]
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            self.state.last_result = error_msg
            return error_msg
