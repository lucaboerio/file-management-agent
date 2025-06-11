import os
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    name: str
    size: int
    modified: float
    created: float
    is_file: bool


class FileTools:
    
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def list_files(self) -> List[FileInfo]:
        files = []
        for item in os.listdir(self.base_dir):
            path = os.path.join(self.base_dir, item)
            if os.path.isfile(path):
                stat = os.stat(path)
                files.append(FileInfo(
                    name=item,
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    created=stat.st_ctime,
                    is_file=True
                ))
        return files
    
    def read_file(self, filename: str) -> str:
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{filename}' not found") 
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write_file(self, filename: str, content: str, mode: str = 'w') -> str:
        if mode not in ['w', 'a']:
            raise ValueError("Mode must be 'w' (write) or 'a' (append)")
        
        path = os.path.join(self.base_dir, filename)
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        return f"File '{filename}' {'created' if mode == 'w' else 'appended'} successfully"
    
    def delete_file(self, filename: str) -> str:
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{filename}' not found")
        
        os.remove(path)
        return f"File '{filename}' deleted successfully"
    
    def answer_question_about_files(self, query: str) -> str:
        query_lower = query.lower()
        files = self.list_files()
        
        if not files:
            return "No files found in the directory."
        
        # Handle common query patterns
        if "how many" in query_lower and "file" in query_lower:
            return f"There are {len(files)} files in the directory."
        
        if "largest" in query_lower or "biggest" in query_lower:
            largest = max(files, key=lambda f: f.size)
            return f"The largest file is '{largest.name}' with {largest.size} bytes."
        
        if "smallest" in query_lower:
            smallest = min(files, key=lambda f: f.size)
            return f"The smallest file is '{smallest.name}' with {smallest.size} bytes."
        
        if "newest" in query_lower or "most recent" in query_lower or "latest" in query_lower:
            newest = max(files, key=lambda f: f.modified)
            mod_time = datetime.fromtimestamp(newest.modified).strftime('%Y-%m-%d %H:%M:%S')
            return f"The most recently modified file is '{newest.name}' (modified: {mod_time})."
        
        if "oldest" in query_lower:
            oldest = min(files, key=lambda f: f.modified)
            mod_time = datetime.fromtimestamp(oldest.modified).strftime('%Y-%m-%d %H:%M:%S')
            return f"The oldest file is '{oldest.name}' (modified: {mod_time})."
        
        if "total size" in query_lower:
            total = sum(f.size for f in files)
            return f"Total size of all files: {total} bytes ({total / 1024:.2f} KB)."
        
        if "list" in query_lower or "show" in query_lower:
            file_list = "\n".join([f"- {f.name} ({f.size} bytes)" for f in files])
            return f"Files in directory:\n{file_list}"
        
        return "I couldn't understand your question. Try asking about file count, sizes, dates, or content searches."
