import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

#from agent.agent import MultiModelFileAgent
from agent.agent_copy import MultiModelFileAgent

async def main():
    work_dir = os.getenv("WORK_DIR") if os.getenv("WORK_DIR") else os.path.join(os.getcwd(), "file_workspace")
    
    print("File Management Agent")
    print(f"Working directory: {work_dir}")
    print("-" * 50)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set!")
        print("Set it with: export OPENAI_API_KEY='your-key' or in .env file")
        print("-" * 50)
    
    agent = MultiModelFileAgent(work_dir, os.getenv("LIGHT_MODEL"), os.getenv("POWERFUL_MODEL"))
    
    print("Commands:")
    print("- Type your request (e.g., 'create a file named test.txt')")
    print("- Type 'exit' or 'quit' to stop")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye :)")
                break
            
            if not user_input:
                continue
            
            response = await agent.process(user_input)
            print(f"\n--> {response}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye :)")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
