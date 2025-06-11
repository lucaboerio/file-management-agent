from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import Tool
from dotenv import load_dotenv
from enum import Enum
import os
import argparse
import asyncio
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from tools.agent_tools import FileTools, FileInfo


load_dotenv()

def load_prompt(filename: str) -> str:
    prompt_path = os.path.join(project_root, "agent", filename)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

class RequestType(Enum):
    INVALID = "invalid"
    SIMPLE = "simple"
    COMPLEX = "complex"

class RequestClassification(BaseModel):
    request_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class MultiModelFileAgent:
    def __init__( self, base_dir: str, light_model: str, powerful_model: str, verbose: bool = False):
        self.light_model = light_model
        self.powerful_model = powerful_model
        self.tools = FileTools(base_dir)
        self.verbose = verbose

        self.classifier = Agent(
            model=light_model,
            deps_type=None,
            output_type=RequestClassification,
            system_prompt=load_prompt("classifier_prompt.txt")
        )
        
        self.main_agent = Agent(
            model=powerful_model,
            deps_type=None,
            output_type=str,
            system_prompt=load_prompt("main_agent_prompt.txt")
        )
        
        self.simple_agent = Agent(
            model=light_model,
            deps_type=None,
            output_type=str,
            system_prompt=load_prompt("simple_agent_prompt.txt")
        )
        
        self.register_tools(self.main_agent, verbose=self.verbose)
        self.register_tools(self.simple_agent, verbose=self.verbose)
    
    def register_tools(self, agent, verbose: bool = False):
        @agent.tool_plain
        def list_files() -> List[Dict[str, Any]]:
            files = self.tools.list_files()
            if verbose:
                print("Listing files")
            return [f.model_dump() for f in files]
        
        @agent.tool_plain
        def read_file(filename: str) -> str:
            if verbose:
                print(f"Reading file: {filename}")
            return self.tools.read_file(filename)
        
        @agent.tool_plain
        def write_file(filename: str, content: str, mode: str = 'w') -> str:
            if verbose:
                print(f"Writing to file: {filename}")
            return self.tools.write_file(filename, content, mode)
        
        @agent.tool_plain
        def delete_file(filename: str) -> str:
            if verbose:
                print(f"Deleting file: {filename}")
            return self.tools.delete_file(filename)
        
        @agent.tool_plain
        def answer_question_about_files(query: str) -> str:
            if verbose:
                print(f"Answering question about files: {query}")
            return self.tools.answer_question_about_files(query)
        


    async def classify_request(self, user_input: str) -> RequestClassification:
        try:
            result = await self.classifier.run(user_input)
            return result.output
        except Exception as e:
            return RequestClassification(
                request_type="complex",
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}, defaulting to complex analysis",
            )
    
    async def handle_invalid_request(self, classification: RequestClassification) -> str:
        if "unrelated" in classification.reasoning.lower():
            return "I'm a file management assistant. I can help you with file operations like reading, writing, listing, and analyzing files in your directory. Please ask me something related to file management."
        
        else:
            return f"I couldn't understand your request. {classification.reasoning} Please rephrase your question more clearly, focusing on what you'd like to do with files."
    
    async def handle_simple_request(self, user_input: str) -> str:
        try:
            result = await self.simple_agent.run(user_input)
            return result.output
        except Exception as e:
            return f"Error handling simple request: {str(e)}"
    
    async def handle_complex_request(self, user_input: str) -> str:
        try:
            result = await self.main_agent.run(user_input)
            return result.output
        except Exception as e:
            return f"Error handling complex request: {str(e)}"
    
    async def process(self, user_input: str, verbose: bool = False) -> str:
        try:
            classification = await self.classify_request(user_input)
            
            if classification.request_type == RequestType.INVALID:
                response = await self.handle_invalid_request(classification)
                
            elif classification.request_type == RequestType.SIMPLE:
                if verbose:
                    print("Using simple agent...")
                response = await self.handle_simple_request(user_input)
                    
            else:
                if verbose:
                    print("Using complex agent...")
                response = await self.handle_complex_request(user_input)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            return error_msg
    
    
def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-model file management agent with intelligent routing",
    )
    
    parser.add_argument(
        "query",
        help="The query to process"
    )
    
    parser.add_argument(
        "--dir",
        default= None,
        help="Base directory for file operations (default: ./file_workspace)"
    )
    
    parser.add_argument(
        "--light-model",
        default="openai:gpt-3.5-turbo",
        help="Light model for classification and simple operations"
    )
    
    parser.add_argument(
        "--powerful-model", 
        default="openai:gpt-4o",
        help="Powerful model for complex operations"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


async def main():
    args = parse_args()
    
    agent = MultiModelFileAgent(
        base_dir=args.dir if args.dir else os.path.join(os.getcwd(), "file_workspace"),
        light_model=args.light_model,
        powerful_model=args.powerful_model
    )
    
    response = await agent.process(args.query, verbose=args.verbose)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
