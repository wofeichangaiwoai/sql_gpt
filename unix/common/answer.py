from tqdm import tqdm

from requests.exceptions import ConnectionError

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import route.router as router
from unix.chain.chain_route import get_route_chain

from datetime import datetime
import os

def get_route_name(question):
    """
       main route based on llm
       input : question
       output: route_name_original 
    """
    try:
        router_chain = get_route_chain()
        route_name_original = router_chain.run(input=str(question), stop=["\n"])
        return route_name_original
    except:
        return "llm connection issue"

def get_answer(question):
    """
        main function used llm capability to answer the questions including general questions and questions related to sql
        input : question
        output: route_name, answer
    """
    answer = ""
    try:
        route_meta = router.get_route_meta()
        route_name = get_route_name(question)
  
        if route_name in route_meta:
            # sql questions
            if "query" == route_name:
                chain_list = route_meta[route_name]
                answer = chain_list.run(question)
            else:
            # general questions
                answer = route_meta[route_name].run(question)
    except ConnectionError as ex:
        answer = f"❌:Connection issue:{type(ex)},{str(ex)}"
        route_name = "error"
    return route_name, answer

if __name__ == '__main__':
    import os
    for _ in tqdm(range(1), desc="Answer testing"):
        if os.environ.get("LLM_TYPE", None) == "din":
            question_list = [
                "what are the revenues for past 3 years"
                ]
            for question in question_list:
               get_answer(question)

"""
   for din_sql: PYTHONPATH=. LLM_TYPE=din python unix/common/answer.py
   for sql chain: PYTHONPATH=. LLM_TYPE=din python unix/common/answer.py
"""
