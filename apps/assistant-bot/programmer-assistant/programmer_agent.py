import os
import subprocess
import asyncio
from typing import List, Dict

class ProgrammerAgent:
    def __init__(self, repo_url, is_private=False, branch=None):
        self.repo_url = repo_url
        self.branch = branch or "feature/ai-update"
        self.local_dir = "/tmp/agent_repo"
        self.is_private = is_private
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.log = []

    def _run(self, cmd: List[str]):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
        return result.stdout.strip()

    def clone_repo(self):
        if os.path.exists(self.local_dir):
            subprocess.run(["rm", "-rf", self.local_dir])
        url = self.repo_url
        if self.is_private and self.github_token:
            url = url.replace("https://", f"https://{self.github_token}@")
        self._run(["git", "clone", url, self.local_dir])
        os.chdir(self.local_dir)
        branches = self._run(["git", "branch", "-r"]).split()
        return branches

    def switch_branch(self):
        os.chdir(self.local_dir)
        self._run(["git", "checkout", "-B", self.branch])

    def scan_files(self):
        self.files = []
        for root, _, files in os.walk(self.local_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html')):
                    self.files.append(os.path.join(root, file))
        return self.files

    def edit_code(self, task_description):
        if not self.files:
            raise RuntimeError("No files found.")
        file_path = self.files[0]
        with open(file_path, "a") as f:
            f.write("\n\n# === AI Agent Edit ===\n")
            f.write(f"# Task: {task_description}\n")
            f.write("print('Code updated by AI agent')\n")
        self._run(["git", "add", "."])
        self._run(["git", "commit", "-m", f"Update: {task_description}"])
        self._run(["git", "push", "--set-upstream", "origin", self.branch])
        return f"Committed to `{self.branch}` and pushed changes."

# Async wrapper
async def run_programmer_flow(repo_url, is_private=False, branch=None, task_description=None):
    agent = ProgrammerAgent(repo_url, is_private=is_private, branch=branch)
    loop = asyncio.get_event_loop()
    
    if not branch:
        branches = await loop.run_in_executor(None, agent.clone_repo)
        files = await loop.run_in_executor(None, agent.scan_files)
        return {"branches": branches, "files": files}

    agent.switch_branch()
    agent.scan_files()
    result = await loop.run_in_executor(None, agent.edit_code, task_description)
    return result
