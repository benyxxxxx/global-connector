from programmer_agent import ProgrammerAgent

# Instantiate a shared ProgrammerAgent to persist state
_programmer_agent = None

def get_programmer_agent(config):
    global _programmer_agent
    if not _programmer_agent:
        _programmer_agent = ProgrammerAgent(config)
    return _programmer_agent
