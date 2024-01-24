
from datetime import datetime

from ubix.chain.chain_din_sql import get_din_chain
from ubix.chain.chain_default import get_default_chain
from ubix.chain.chain_route import get_route_chain
from ubix.chain.chain_sql_ubix import get_db_chain
from ubix.common.llm import llm
from tqdm import tqdm
import os

router_chain = get_route_chain(llm)
default_chain = get_default_chain(llm)

def get_route_meta():
    """
        two route: sql route and general route
    """
    llm_type = os.environ.get("LLM_TYPE")
    route_meta = {
        # get_din_chain use din_sql to generate the sql
        # get_db_chain use sqlchain to generate the sql
        "query": get_din_chain(llm) if llm_type == "din" else get_db_chain(llm),
        "other": get_default_chain(llm),
    }
    assert all(route_meta.values()), f"❌One of the value is None in route_mate, LLM_TYPE:{llm_type}"
    return route_meta


if __name__ == '__main__':
    route_meta = get_route_meta()
    for _ in tqdm(range(1)):
        question_list = [
            "How many records in this table",
            ]
        for question in question_list:
            start_route = datetime.now()
            route_name = router_chain.run(question)
            route_name = route_name if route_name in route_meta else "DEFAULT"
            start = datetime.now()
            duration_route = (start-start_route).total_seconds()
            print(f'>>>: Begin ask {route_name} about question: {question}, route cost:{duration_route} ')
            if route_name in route_meta:
                answer = route_meta[route_name].run(question)
            else:
                answer = get_default_chain(llm).run(question)
            end = datetime.now()
            duration = (end-start).total_seconds()
            print(f'>>>: End ask {route_name} about question {question}, cost:{duration} sec, answer: {answer}')
            print(">>>>>>"*10 + f"Route:{route_name} cost:{duration_route:.0f} seconds, Query: cost:{duration:.0f} sec seconds")



"""
CUDA_VISIBLE_DEVICES=1 LLM_TYPE=gglm PYTHONPATH=. python route/router.py
CUDA_VISIBLE_DEVICES=1 LLM_TYPE=vllm PYTHONPATH=. python route/router.py
"""
