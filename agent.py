from vendors.myOA import Agent as GptAgent
from vendors.myClaude import Agent as ClaudeAgent
from vendors.myLlama import Agent as LlamaAgent
from vendors.myPerplexity import Agent as PerplexityAgent
agent_classes = {
    'llama': LlamaAgent,
    'claude': ClaudeAgent,
    'gpt': GptAgent,
    'perplex':PerplexityAgent,
    'gemini':GptAgent,
    'grok':GptAgent,
}
from models import model_ids


def initialize_agent(model='gpt-4o-mini',max_tokens=4096,temperature=.5,system_prompt='You are a helpful assistant',messages=[]):
    
    AgentClass = agent_classes[model_ids[model]['vendor']]

    return AgentClass(model=model, max_tokens=max_tokens, messages=messages,
                      temperature=temperature, system_prompt=system_prompt)


