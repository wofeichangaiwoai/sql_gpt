from langchain import LLMChain
from unix.common.llm import llm
from langchain.prompts import PromptTemplate

template = """you are a chatbot having a conversation with a human.

Human: {question}
Chatbot:"""

def get_default_chain(llm):
    """
        set a default_chain for general questions
    """
    prompt = PromptTemplate(
        input_variables=["question"], template=template
    )
    chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    return chain


if __name__ == '__main__':
    default_chain = get_default_chain(llm)
