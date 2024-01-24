from datetime import datetime

from sqlalchemy.engine import create_engine
from trino.sqlalchemy import URL

from unix.chain.sql.sql_base import SQLDatabaseChainEx, SQLDatabaseEx
from unix.common.llm import llm

def get_db_chain(llm):
    hive_host = ""
    port = 8080
    user_name = ""
    catalog=""
    include_tables = [""]
    hive_database = ""
    engine = create_engine(
        URL(
            host=hive_host,
            port=port,
            user=user_name,
            catalog=catalog,
            schema=hive_database,
        ),
    )
    sql_db = SQLDatabaseEx(engine, schema=hive_database, include_tables=include_tables)
    db_chain = SQLDatabaseChainEx.from_llm(llm=llm, db=sql_db, verbose=True)
    return db_chain


if __name__ == "__main__":

    print(datetime.now())
    start = datetime.now()
    agent = get_db_chain(llm)
    """
    query = "how many records are there in this table?"
    print(datetime.now())
    
    agent.run(query)
    """
    query = "what is the maximum total in this table?"
    answer = agent.run(query)
    print(datetime.now())
    """
    query = "What is the maximum total  in the city Novi"
    agent.run(query)
    print(datetime.now())
    """
    end = datetime.now()
    duration = (end-start).total_seconds()
    logging.info("🔴 answer:\n" + answer)
    logging.info("⏰ " + f"Query: cost:{duration:.0f} sec seconds")

"""
PYTHONPATH=.  LLM_TYPE=tgi python unix/chain/chain_sql_ubix.py
"""
