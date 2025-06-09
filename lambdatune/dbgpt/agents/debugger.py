from typing import Optional, Any

from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import create_react_agent

class PostgresDBExplorer(BaseTool):
    """Tool that allows you to execute queries against a Postgres database."""

    name: str = "postgres_db_explorer"
    description: str = (
        "This tool executes a query in Postgres. It returns back the execution plan in the EXPLAIN ANALYZE format."
    )

    # Declare private attributes
    from pydantic import PrivateAttr

    _cursor: Any = PrivateAttr()
    _query: str = PrivateAttr()

    def __init__(self, cursor, query, **kwargs):
        super().__init__(**kwargs)
        self._cursor = cursor
        self._query = query

    def _run(
        self,
        settings: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Use the tool to execute a query and return the execution plan.
        Args:
            settings (str): The settings to apply to the query execution. Should be provided as a string
             with \n linebreaks and a semicolon at the end of each setting.
        """
        for setting in settings.splitlines():
            if setting.strip():
                self._cursor.execute(setting.strip())

        self._cursor.execute("EXPLAIN ANALYZE " + self._query)
        result = ""
        for row in self._cursor.fetchall():
            result += str(row[0]) + "\n"
        return result

    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""

        return None

class DebuggingAgent:
    def __init__ (self, query, cursor, fast_plan, slow_plan):
        tools = [PostgresDBExplorer(query=query, cursor=cursor)]

        # Choose the LLM that will drive the agent
        llm = ChatOpenAI(model="gpt-4-turbo-preview")
        prompt = "You are a Database Administrator and a helpful assistant. You can execute queries against a Postgres database and search the web for information."

        self.agent_executor = create_react_agent(llm, tools, prompt=prompt)

        self.prompt =  f"""
        My query suddenly started running very slow. Here is the fastest plan we've seen for that query:
        
        {fast_plan}
        
        Here is the slow plan
        
        {slow_plan}
        
        I need to find a good configuration settings to optimize my query on Postgres. You are provided with a set of tools
        that allow you to execute the query. You do not have access to the query but you can call the PostgresDBExplorer tool 
        to get the execution plan of the query. Try out different settings and return the best one you can find.
        
        If you use the Postgres Tool, generated the settings you'd like to try out as a single string with linebreaks and
        a semicolon at the end of each setting. For example:
        SET work_mem = '64MB';
        SET effective_cache_size = '4GB';
        SET maintenance_work_mem = '1GB';
        """

    def debug(self):
        r = self.agent_executor.invoke({"messages": [("user", self.prompt)]})
        return r["messages"]