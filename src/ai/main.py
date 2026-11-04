
import os, sys
import argparse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from GlobalEnv import GlobalEnv
from config.ConfigFile import ConfigScope

from ai.agents import IterativeAgent
from ai.models import OllamaLocalModel, OllamaCloudModel

import re

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="AI Agent CLI")
    parser.add_argument('query', nargs='+', help="The query to ask the agent")
    args = parser.parse_args()

    agentQuery = " ".join(args.query)

    ollamaModel = OllamaCloudModel('gemma4:cloud')
    if GlobalEnv().currentScope.includes(ConfigScope.HOME_PC):
        ollamaModel = OllamaLocalModel('qwen2.5-coder:14b')

    agent = IterativeAgent(ollamaModel)
    response: str = agent.ask(agentQuery)

    print(end="\n\n", file=sys.stderr, flush=True)
    print(response, file=sys.stdout, flush=True)