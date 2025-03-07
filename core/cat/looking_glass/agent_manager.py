# import re
from copy import copy

from cat.log import log
from langchain.agents import AgentExecutor, ConversationalAgent
from langchain.chains import LLMChain


class AgentManager:
    def __init__(self, cat):
        self.cat = cat

    def get_agent_executor(self):
        mad_hatter = self.cat.mad_hatter

        prompt_prefix = mad_hatter.execute_hook("agent_prompt_prefix") + "\n# Tools:"
        prompt_format_instructions = mad_hatter.execute_hook("agent_prompt_instructions")
        prompt_suffix = mad_hatter.execute_hook("agent_prompt_suffix")

        # extract automatically input_variables from prompt parts (can't do it yet)
        # full_prompt_content = prompt_prefix + prompt_format_instructions + prompt_suffix
        # input_variables = re.findall(r'\{(.*?)\}', full_prompt_content)
        # input_variables = list(filter(lambda v: ("'" not in v) and ('"' not in v), input_variables)) # avoid problems if prompt contains an example dictionary/JSON
        # log('INPUT VARIABLES')
        # log(input_variables)
        input_variables = [
            "input",
            "chat_history",
            "episodic_memory",
            "declarative_memory",
            "agent_scratchpad",
        ]

        input_variables = mad_hatter.execute_hook("before_agent_creates_prompt", input_variables,
                                                  " ".join([prompt_prefix, prompt_format_instructions, prompt_suffix]))

        allowed_tools = mad_hatter.execute_hook("agent_allowed_tools")
        allowed_tools_names = [t.name for t in allowed_tools]

        prompt = ConversationalAgent.create_prompt(
            tools=allowed_tools,
            prefix=prompt_prefix,
            format_instructions=prompt_format_instructions,
            suffix=prompt_suffix,
            ai_prefix="AI",
            human_prefix="Human",
            input_variables=input_variables,
        )

        log("Sending prompt", "INFO")
        log(prompt.template, "DEBUG")

        # main chain
        agent_chain = LLMChain(prompt=prompt, llm=self.cat.llm, verbose=True)

        # init agent
        agent = ConversationalAgent(
            llm_chain=agent_chain,
            allowed_tools=allowed_tools_names,
            verbose=True
        )

        # agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=allowed_tools,
            return_intermediate_steps=True,
            verbose=True
        )

        return agent_executor
