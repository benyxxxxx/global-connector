import os
import httpx
import tempfile
import shutil
from fastapi import FastAPI, Request
from openai import OpenAI
from typing import Dict
from set_commands import set_bot_commands
import git
from github import Github
import asyncio
from pathlib import Path

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "")
TELEGRAM_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://assistant-bot-dev.fly.dev/webhook")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

app = FastAPI()

async def set_telegram_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    async with httpx.AsyncClient() as client:
        res = await client.post(url, params={"url": TELEGRAM_WEBHOOK_URL})
        print("✅ Webhook set:", res.json())

@app.on_event("startup")
async def startup():
    await set_bot_commands()
    await set_telegram_webhook()
    print("✅ Bot commands set successfully.")

# Initialize hardcoded programmer agent
AGENTS: Dict[str, Dict] = {
    "programmer": {
        "description": "Expert programmer agent that can clone GitHub repositories, make changes, and push code updates. Specializes in code analysis, file creation, modification, and Git operations.",
        "is_private": False,
        "owner_id": 0,  # System agent
        "is_system": True
    }
}

USER_SESSIONS: Dict[int, Dict] = {}

class GitHubManager:
    def __init__(self, token: str):
        self.github = Github(token)
        self.token = token
    
    def validate_repo_url(self, url: str) -> tuple[bool, str, str]:
        """Validate GitHub repository URL and extract owner/repo"""
        try:
            # Extract owner and repo from various GitHub URL formats
            if "github.com" in url:
                # Handle https://github.com/owner/repo format
                parts = url.split("github.com/")[1].split("/")
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = parts[1].replace(".git", "")
                    return True, owner, repo
            return False, "", ""
        except:
            return False, "", ""
    
    def check_repo_exists(self, owner: str, repo: str) -> bool:
        """Check if repository exists and is accessible"""
        try:
            self.github.get_repo(f"{owner}/{repo}")
            return True
        except:
            return False
    
    def get_repo_branches(self, owner: str, repo: str) -> list:
        """Get list of branches in repository"""
        try:
            repo_obj = self.github.get_repo(f"{owner}/{repo}")
            branches = [branch.name for branch in repo_obj.get_branches()]
            return branches
        except:
            return []

class GitOperations:
    def __init__(self, repo_path: str, github_token: str):
        self.repo_path = repo_path
        self.github_token = github_token
        self.repo = None
    
    def clone_repo(self, repo_url: str) -> bool:
        """Clone repository to local path"""
        try:
            # Add token to URL for authentication
            if "https://github.com" in repo_url:
                auth_url = repo_url.replace("https://github.com", f"https://{self.github_token}@github.com")
            else:
                auth_url = repo_url
            
            self.repo = git.Repo.clone_from(auth_url, self.repo_path)
            return True
        except Exception as e:
            print(f"Clone error: {e}")
            return False
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to specified branch"""
        try:
            if not self.repo:
                return False
            
            # Check if branch exists locally
            if branch_name in [head.name for head in self.repo.heads]:
                self.repo.git.checkout(branch_name)
            else:
                # Try to checkout remote branch
                try:
                    self.repo.git.checkout(f"origin/{branch_name}", b=branch_name)
                except:
                    return False
            return True
        except:
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """Create and switch to new branch"""
        try:
            if not self.repo:
                return False
            
            self.repo.git.checkout(b=branch_name)
            return True
        except:
            return False
    
    def read_repo_structure(self) -> str:
        """Read and return repository structure"""
        try:
            structure = []
            for root, dirs, files in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                
                level = root.replace(self.repo_path, '').count(os.sep)
                indent = ' ' * 2 * level
                structure.append(f"{indent}{os.path.basename(root)}/")
                
                subindent = ' ' * 2 * (level + 1)
                for file in files[:10]:  # Limit to first 10 files per directory
                    structure.append(f"{subindent}{file}")
                
                if len(files) > 10:
                    structure.append(f"{subindent}... and {len(files) - 10} more files")
            
            return "\n".join(structure[:50])  # Limit output
        except:
            return "Could not read repository structure"
    
    def create_file(self, file_path: str, content: str = "") -> bool:
        """Create file with content"""
        try:
            full_path = os.path.join(self.repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Create file error: {e}")
            return False
    
    def create_directory(self, dir_path: str) -> bool:
        """Create directory"""
        try:
            full_path = os.path.join(self.repo_path, dir_path)
            os.makedirs(full_path, exist_ok=True)
            return True
        except:
            return False
    
    def stage_changes(self) -> bool:
        """Stage all changes"""
        try:
            if not self.repo:
                return False
            self.repo.git.add(A=True)
            return True
        except:
            return False
    
    def commit_changes(self, message: str) -> bool:
        """Commit staged changes"""
        try:
            if not self.repo:
                return False
            
            # Check if there are changes to commit
            if self.repo.is_dirty() or self.repo.untracked_files:
                self.repo.index.commit(message)
                return True
            return False  # No changes to commit
        except Exception as e:
            print(f"Commit error: {e}")
            return False
    
    def push_changes(self) -> bool:
        """Push changes to remote"""
        try:
            if not self.repo:
                return False
            
            # Get current branch
            current_branch = self.repo.active_branch.name
            origin = self.repo.remote(name='origin')
            origin.push(current_branch)
            return True
        except Exception as e:
            print(f"Push error: {e}")
            return False

github_manager = GitHubManager(GITHUB_TOKEN) if GITHUB_TOKEN else None

async def send_telegram_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": text})

async def ask_openai(prompt: str, system_prompt: str = "") -> str:
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            extra_headers={
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_SITE_NAME,
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
        return "⚠️ Failed to get response from the agent."

async def process_code_changes(user_request: str, git_ops: GitOperations) -> str:
    """Process user's code change request using AI"""
    try:
        # Get current repo structure
        repo_structure = git_ops.read_repo_structure()
        
        # Create a prompt for the AI to understand what changes to make
        system_prompt = f"""You are a programming assistant. The user has a repository with this structure:

{repo_structure}

The user wants to make changes to the repository. Analyze their request and provide specific instructions on what files/folders to create or modify.

Respond in this format:
ACTION_TYPE: CREATE_FILE|CREATE_DIR|MODIFY_FILE
PATH: relative/path/from/repo/root
CONTENT: (only for files, can be empty)

You can provide multiple actions separated by ---

Example:
ACTION_TYPE: CREATE_DIR
PATH: utils
CONTENT: 

---

ACTION_TYPE: CREATE_FILE  
PATH: utils/helper.py
CONTENT: # Helper utilities
def example_function():
    pass
"""

        response = await ask_openai(user_request, system_prompt)
        
        # Parse and execute the AI's instructions
        actions = response.split("---")
        results = []
        
        for action in actions:
            lines = [line.strip() for line in action.strip().split("\n") if line.strip()]
            if len(lines) < 2:
                continue
                
            action_type = ""
            path = ""
            content = ""
            
            for line in lines:
                if line.startswith("ACTION_TYPE:"):
                    action_type = line.split(":", 1)[1].strip()
                elif line.startswith("PATH:"):
                    path = line.split(":", 1)[1].strip()
                elif line.startswith("CONTENT:"):
                    content = line.split(":", 1)[1].strip()
                elif content and not line.startswith(("ACTION_TYPE:", "PATH:")):
                    content += "\n" + line
            
            if not action_type or not path:
                continue
                
            if action_type == "CREATE_DIR":
                if git_ops.create_directory(path):
                    results.append(f"✅ Created directory: {path}")
                else:
                    results.append(f"❌ Failed to create directory: {path}")
                    
            elif action_type == "CREATE_FILE":
                if git_ops.create_file(path, content):
                    results.append(f"✅ Created file: {path}")
                else:
                    results.append(f"❌ Failed to create file: {path}")
                    
            elif action_type == "MODIFY_FILE":
                if git_ops.create_file(path, content):  # This will overwrite existing file
                    results.append(f"✅ Modified file: {path}")
                else:
                    results.append(f"❌ Failed to modify file: {path}")
        
        return "\n".join(results) if results else "❌ No valid actions found in AI response"
        
    except Exception as e:
        return f"❌ Error processing changes: {e}"

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message")
    if not message or "text" not in message:
        return {"status": "ignored"}

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message["text"].strip()
    session = USER_SESSIONS.get(user_id)

    # === COMMANDS: always checked FIRST ===
    if text.startswith("/createagent"):
        USER_SESSIONS[user_id] = {"state": "create_name"}
        await send_telegram_message(chat_id, "🆕 Enter agent name:")
        return {"status": "ok"}

    if text.startswith("/editagent"):
        USER_SESSIONS[user_id] = {"state": "edit_ask_name"}
        await send_telegram_message(chat_id, "✏️ Enter the name of the agent you want to edit:")
        return {"status": "ok"}

    if text.startswith("/deleteagent"):
        USER_SESSIONS[user_id] = {"state": "delete_ask_name"}
        await send_telegram_message(chat_id, "🗑️ Enter the name of the agent you want to delete:")
        return {"status": "ok"}

    if text.startswith("/useagent"):
        USER_SESSIONS[user_id] = {"state": "use_ask_name"}
        await send_telegram_message(chat_id, "🤖 Enter the name of the agent you want to use:")
        return {"status": "ok"}

    if text.startswith("/listagent"):
        visible_agents = [
            f"🔹 *{name}*\n📝 {details['description']}\n🔒 {'Private' if details['is_private'] else 'Public'}"
            for name, details in AGENTS.items()
            if not details["is_private"] or details["owner_id"] == user_id or details.get("is_system", False)
        ]
        response = "\n\n".join(visible_agents) if visible_agents else "No agents available."
        await send_telegram_message(chat_id, response)
        return {"status": "ok"}

    # === HANDLE SESSION STATES ===
    if session:
        state = session.get("state")

        # Existing agent creation/editing states
        if state == "create_name":
            session["agent_name"] = text
            session["state"] = "create_description"
            await send_telegram_message(chat_id, "📝 Enter agent description:")
            return {"status": "ok"}

        if state == "create_description":
            session["agent_description"] = text
            session["state"] = "create_privacy"
            await send_telegram_message(chat_id, "🔒 Should this agent be private? (yes/no):")
            return {"status": "ok"}

        if state == "create_privacy":
            is_private = text.lower() in ["yes", "true", "1"]
            name = session["agent_name"]
            AGENTS[name] = {
                "description": session["agent_description"],
                "is_private": is_private,
                "owner_id": user_id
            }
            USER_SESSIONS.pop(user_id, None)
            await send_telegram_message(chat_id, f"✅ Agent '{name}' created.")
            return {"status": "ok"}

        if state == "edit_ask_name":
            agent = AGENTS.get(text)
            if not agent:
                await send_telegram_message(chat_id, f"❌ Agent '{text}' not found.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            if agent["owner_id"] != user_id and not agent.get("is_system", False):
                await send_telegram_message(chat_id, "❌ You are not the owner of this agent.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            if agent.get("is_system", False):
                await send_telegram_message(chat_id, "❌ System agents cannot be edited.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            session["agent_name"] = text
            session["state"] = "edit_name"
            await send_telegram_message(chat_id, f"✏️ Editing '{text}'. Enter new name (or send the same):")
            return {"status": "ok"}

        if state == "edit_name":
            session["new_name"] = text
            session["state"] = "edit_description"
            await send_telegram_message(chat_id, "📝 Enter new description:")
            return {"status": "ok"}

        if state == "edit_description":
            session["new_description"] = text
            session["state"] = "edit_privacy"
            await send_telegram_message(chat_id, "🔒 Should this agent be private? (yes/no):")
            return {"status": "ok"}

        if state == "edit_privacy":
            is_private = text.lower() in ["yes", "true", "1"]
            old_name = session["agent_name"]
            new_name = session.get("new_name", old_name)
            agent_data = AGENTS.pop(old_name)
            AGENTS[new_name] = agent_data
            AGENTS[new_name]["description"] = session.get("new_description", agent_data["description"])
            AGENTS[new_name]["is_private"] = is_private
            AGENTS[new_name]["owner_id"] = user_id
            USER_SESSIONS.pop(user_id, None)
            await send_telegram_message(chat_id, f"✅ Agent '{new_name}' updated.")
            return {"status": "ok"}

        if state == "delete_ask_name":
            agent = AGENTS.get(text)
            if not agent:
                await send_telegram_message(chat_id, f"❌ Agent '{text}' not found.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            if agent["owner_id"] != user_id and not agent.get("is_system", False):
                await send_telegram_message(chat_id, "❌ You are not the owner of this agent.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            if agent.get("is_system", False):
                await send_telegram_message(chat_id, "❌ System agents cannot be deleted.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            AGENTS.pop(text)
            if session.get("agent_name") == text:
                USER_SESSIONS.pop(user_id, None)
            await send_telegram_message(chat_id, f"🗑️ Agent '{text}' deleted.")
            USER_SESSIONS.pop(user_id, None)
            return {"status": "ok"}

        if state == "use_ask_name":
            agent = AGENTS.get(text)
            if not agent:
                await send_telegram_message(chat_id, f"❌ Agent '{text}' not found.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            if agent["is_private"] and agent["owner_id"] != user_id and not agent.get("is_system", False):
                await send_telegram_message(chat_id, "🔒 This agent is private.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            # Special handling for programmer agent
            if text == "programmer":
                if not GITHUB_TOKEN:
                    await send_telegram_message(chat_id, "❌ GitHub token not configured. Please contact administrator.")
                    USER_SESSIONS.pop(user_id, None)
                    return {"status": "ok"}
                
                USER_SESSIONS[user_id] = {"state": "programmer_ask_repo", "agent_name": text}
                await send_telegram_message(chat_id, "👨‍💻 Welcome to Programmer Agent! Please provide the GitHub repository URL:")
                return {"status": "ok"}
            else:
                USER_SESSIONS[user_id] = {"state": "using_agent", "agent_name": text}
                await send_telegram_message(chat_id, f"✅ Now chatting with '{text}'. Ask me anything!")
                return {"status": "ok"}

        # Programmer agent workflow states
        if state == "programmer_ask_repo":
            if not github_manager:
                await send_telegram_message(chat_id, "❌ GitHub integration not available.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            # Validate GitHub repo URL
            is_valid, owner, repo = github_manager.validate_repo_url(text)
            if not is_valid:
                await send_telegram_message(chat_id, "❌ Invalid GitHub repository URL. Please provide a valid URL like: https://github.com/owner/repo")
                return {"status": "ok"}
            
            # Check if repo exists
            if not github_manager.check_repo_exists(owner, repo):
                await send_telegram_message(chat_id, f"❌ Repository '{owner}/{repo}' not found or not accessible.")
                return {"status": "ok"}
            
            # Store repo info and create temp directory
            temp_dir = tempfile.mkdtemp(prefix=f"repo_{owner}_{repo}_")
            session["repo_url"] = text
            session["repo_owner"] = owner
            session["repo_name"] = repo
            session["temp_dir"] = temp_dir
            session["state"] = "programmer_cloning"
            
            await send_telegram_message(chat_id, f"✅ Repository found: {owner}/{repo}\n🔄 Cloning repository...")
            
            # Clone repository
            git_ops = GitOperations(temp_dir, GITHUB_TOKEN)
            if git_ops.clone_repo(text):
                session["git_ops"] = git_ops
                session["state"] = "programmer_ask_branch"
                
                # Get available branches
                branches = github_manager.get_repo_branches(owner, repo)
                branch_list = ", ".join(branches[:10])  # Show first 10 branches
                
                repo_structure = git_ops.read_repo_structure()
                await send_telegram_message(chat_id, f"✅ Repository cloned successfully!\n\n📁 Repository structure:\n```\n{repo_structure}\n```\n\n🌿 Available branches: {branch_list}\n\nWhich branch do you want to work on?")
            else:
                await send_telegram_message(chat_id, "❌ Failed to clone repository. Please check the URL and permissions.")
                USER_SESSIONS.pop(user_id, None)
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {"status": "ok"}

        if state == "programmer_ask_branch":
            git_ops = session.get("git_ops")
            if not git_ops:
                await send_telegram_message(chat_id, "❌ Git operations not initialized.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            # Switch to specified branch
            if git_ops.switch_branch(text):
                session["current_branch"] = text
                session["state"] = "programmer_ask_changes"
                await send_telegram_message(chat_id, f"✅ Switched to branch: {text}\n\nWhat changes would you like to make? Please describe what you want to do (e.g., 'create a utils folder with helper.py file containing basic utility functions'):")
            else:
                await send_telegram_message(chat_id, f"❌ Branch '{text}' not found. Please enter a valid branch name or create a new one by typing: 'create new branch <branch_name>'")
            
            return {"status": "ok"}

        if state == "programmer_ask_changes":
            git_ops = session.get("git_ops")
            if not git_ops:
                await send_telegram_message(chat_id, "❌ Git operations not initialized.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            await send_telegram_message(chat_id, "🔄 Processing your request...")
            
            # Process the changes using AI
            result = await process_code_changes(text, git_ops)
            
            session["state"] = "programmer_ask_commit_type"
            await send_telegram_message(chat_id, f"Changes made:\n{result}\n\nHow would you like to save these changes?\n1. Commit to current branch ({session.get('current_branch', 'unknown')})\n2. Create new branch and commit\n\nType '1' or '2':")
            
            return {"status": "ok"}

        if state == "programmer_ask_commit_type":
            git_ops = session.get("git_ops")
            if not git_ops:
                await send_telegram_message(chat_id, "❌ Git operations not initialized.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            if text == "1":
                session["state"] = "programmer_ask_commit_message"
                await send_telegram_message(chat_id, "📝 Enter commit message:")
            elif text == "2":
                session["state"] = "programmer_ask_new_branch"
                await send_telegram_message(chat_id, "🌿 Enter new branch name:")
            else:
                await send_telegram_message(chat_id, "Please type '1' for current branch or '2' for new branch.")
            
            return {"status": "ok"}

        if state == "programmer_ask_new_branch":
            git_ops = session.get("git_ops")
            if not git_ops:
                await send_telegram_message(chat_id, "❌ Git operations not initialized.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            if git_ops.create_branch(text):
                session["current_branch"] = text
                session["state"] = "programmer_ask_commit_message"
                await send_telegram_message(chat_id, f"✅ Created and switched to new branch: {text}\n📝 Enter commit message:")
            else:
                await send_telegram_message(chat_id, f"❌ Failed to create branch '{text}'. Please try a different name.")
            
            return {"status": "ok"}

        if state == "programmer_ask_commit_message":
            git_ops = session.get("git_ops")
            if not git_ops:
                await send_telegram_message(chat_id, "❌ Git operations not initialized.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            
            commit_message = text
            
            await send_telegram_message(chat_id, "🔄 Staging, committing, and pushing changes...")
            
            # Stage changes
            if not git_ops.stage_changes():
                await send_telegram_message(chat_id, "❌ Failed to stage changes.")
                return {"status": "ok"}
            
            # Commit changes
            if not git_ops.commit_changes(commit_message):
                await send_telegram_message(chat_id, "⚠️ No changes to commit or commit failed.")
                return {"status": "ok"}
            
            # Push changes
            if git_ops.push_changes():
                current_branch = session.get("current_branch", "unknown")
                repo_owner = session.get("repo_owner", "")
                repo_name = session.get("repo_name", "")
                
                await send_telegram_message(chat_id, f"✅ Successfully pushed changes!\n\n🌿 Branch: {current_branch}\n💬 Commit: {commit_message}\n🔗 Repository: {repo_owner}/{repo_name}\n\n✨ All operations completed successfully!")
                
                # Clean up
                temp_dir = session.get("temp_dir")
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                USER_SESSIONS.pop(user_id, None)
            else:
                await send_telegram_message(chat_id, "❌ Failed to push changes. Please check repository permissions.")
            
            return {"status": "ok"}

        # Regular agent usage
        if state == "using_agent":
            agent_name = session["agent_name"]
            agent = AGENTS.get(agent_name)
            if not agent:
                await send_telegram_message(chat_id, "❌ Agent not found.")
                USER_SESSIONS.pop(user_id, None)
                return {"status": "ok"}
            reply = await ask_openai(prompt=text, system_prompt=agent["description"])
            await send_telegram_message(chat_id, reply)
            return {"status": "ok"}

    # Default fallback
    await send_telegram_message(chat_id, "🤖 Unrecognized command. Type `/` to see available actions.")
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Bot is running. Set webhook to /webhook"}