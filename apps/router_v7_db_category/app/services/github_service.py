import os
import aiohttp

GITHUB_OWNER = os.environ.get("GITHUB_OWNER")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_WORKFLOW_FILE = os.environ.get("GITHUB_WORKFLOW_FILE", "deploy.yml")

async def trigger_deployment_workflow(fly_config: str, ref: str = "main"):
    if not all([GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN]):
        print("GitHub environment variables are not configured.")
        return None

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW_FILE}/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
    }
    payload = {"ref": ref, "inputs": {"fly_config": fly_config}}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 204:
                return f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW_FILE}"
            else:
                print(f"Error triggering workflow: {await response.text()}")
                return None