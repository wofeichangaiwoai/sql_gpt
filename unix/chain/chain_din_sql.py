
import datetime
from typing import Any, Dict, List, Optional
import pdb
from langchain.prompts import PromptTemplate
from pydantic import Extra
from sqlalchemy.engine import create_engine
from trino.sqlalchemy import URL
from sqlalchemy import *
from langchain.schema.language_model import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain
from langchain.prompts.base import BasePromptTemplate

from unix.common.llm import llm

"""
   easy_template and hard_template are few shot prompt for generating sql
   easy_template contains join
   hard_template doesn't contain join
"""

easy_template = """
# Use the the schema links to generate the SQL queries for each of the questions.
Q: "Find the buildings which have rooms with capacity more than 50."
Schema_links: [classroom.building,classroom.capacity,50]
SQL: SELECT DISTINCT building FROM classroom WHERE capacity  >  50

Q: "Find the room number of the rooms which can sit 50 to 100 students and their buildings."
Schema_links: [classroom.building,classroom.room_number,classroom.capacity,50,100]
SQL: SELECT building ,  room_number FROM classroom WHERE capacity BETWEEN 50 AND 100

Q: "Give the name of the student in the History department with the most credits."
Schema_links: [student.name,student.dept_name,student.tot_cred,History]
SQL: SELECT name FROM student WHERE dept_name  =  'History' ORDER BY tot_cred DESC LIMIT 1

Q: "Find the total budgets of the Marketing or Finance department."
Schema_links: [department.budget,department.dept_name,Marketing,Finance]
SQL: SELECT sum(budget) FROM department WHERE dept_name  =  'Marketing' OR dept_name  =  'Finance'

Q: "Find the department name of the instructor whose name contains 'Soisalon'."
Schema_links: [instructor.dept_name,instructor.name,Soisalon]
SQL: SELECT dept_name FROM instructor WHERE name LIKE '%Soisalon%'

Q: "What is the name of the department with the most credits?"
Schema_links: [course.dept_name,course.credits]
SQL: SELECT dept_name FROM course GROUP BY dept_name ORDER BY sum(credits) DESC LIMIT 1

Q: "How many instructors teach a course in last year?"
Schema_links: [teaches.ID,teaches.semester,teaches.YEAR,Spring,2022]
SQL: SELECT COUNT (DISTINCT ID) FROM teaches WHERE semester  =  'Spring' AND YEAR  =  2022

Q: "Find the name of the students and their department names sorted by their total credits in ascending order."
Schema_links: [student.name,student.dept_name,student.tot_cred]
SQL: SELECT name ,  dept_name FROM student ORDER BY tot_cred

Q: "Find the year which offers the largest number of courses."
Schema_links: [SECTION.YEAR,SECTION.*]
SQL: SELECT YEAR FROM SECTION GROUP BY YEAR ORDER BY count(*) DESC LIMIT 1

Q: "What are the names and average salaries for departments with average salary higher than 42000?"
Schema_links: [instructor.dept_name,instructor.salary,42000]
SQL: SELECT dept_name ,  AVG (salary) FROM instructor GROUP BY dept_name HAVING AVG (salary)  >  42000

Q: "How many rooms in each building have a capacity of over 50?"
Schema_links: [classroom.*,classroom.building,classroom.capacity,50]
SQL: SELECT count(*) ,  building FROM classroom WHERE capacity  >  50 GROUP BY building

Q: "Find the names of the top 3 departments that provide the largest amount of courses?"
Schema_links: [course.dept_name,course.*]
SQL: SELECT dept_name FROM course GROUP BY dept_name ORDER BY count(*) DESC LIMIT 3

Q: "Find the maximum and average capacity among rooms in each building."
Schema_links: [classroom.building,classroom.capacity]
SQL: SELECT max(capacity) ,  avg(capacity) ,  building FROM classroom GROUP BY building

Q: "Find the title of the course that is offered by more than one department."
Schema_links: [course.title]
SQL: SELECT title FROM course GROUP BY title HAVING count(*)  >  1

Q: "show the revenues in last three year?"
Schema_links: [product.avenue, 2022, 2019, product.date]
SQL: SELECT year(product.date), max(avenue) from product where date between '2019-01-01 00:00:00' and '2022-12-31 23:59:59' GROUP BY year(product.date)

Q: "{input}"
schema_links: [{schema_links}]
SQL:
"""

hard_template = """
Q: "Find the title of courses that have two prerequisites?"
Schema_links: [course.title,course.course_id = prereq.course_id]
SQL: SELECT course.title, prereq.course_id FROM course, prereq WHERE course.course_id  =  prereq.course_id GROUP BY prereq.course_id HAVING count(*)  =  2

Q: "Find the total number of students and total number of instructors for each department."
Schema_links: [department.dept_name = student.dept_name,student.id,department.dept_name = instructor.dept_name,instructor.id]
SQL: SELECT count(DISTINCT student.id), count(DISTINCT instructor.id), instructor.dept_name FROM department, student, instructor WHERE department.dept_name = instructor.dept_name and department.dept_name = student.dept_name GROUP BY instructor.dept_name

Q: "What are salaries and by employees and cityname employees live in for the past three years?"
Schema_links: [company.salary,company.employee_id=employee.employee_id,company.YEAR,employee.name,city.city_id=employee.city_id,city.name]
SQL: SELECT year(company.YEAR),employee.name,city.name,sum(company.salary) FROM company,employee,city WHERE company.employee_id=employee.employee_id and city.city_id=employee.city_id and company.YEAR between '2019-01-01 00:00:00' and '2022-12-31 23:59:59' GROUP BY year(company.YEAR),employee.name,city.name

Q: "Find the name of students who took any class in past three years"
Schema_links: [student.name,student.id = takes.id,takes.YEAR]
SQL: SELECT year(takes.YEAR),DISTINCT student.name FROM student,takes WHERE student.id = takes.id and takes.YEAR  between '2019-01-01 00:00:00' and '2022-12-31 23:59:59' GROUP BY year(takes.YEAR)

Q: "{input}"
Schema_links:{schema_links}
SQL:
"""

product_schema = """
Q: "Show the revenue by product for past year"
A: Let�~@~Ys think step by step. In the question "Show the revenues by product for past year", we are asked:
"the revenue" so we need column = [invoice_items.netamount,invoice_items.productid,invoice_items.description]
"by product" so we need column = [invoice_header.objectid]
"for past year" so we need column = [invoice_header.creationdatetime]
Based on the columns and tables, we need these Foreign_keys = [invoice_items.parentobjectid=invoice_header.objectid].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [1]. So the Schema_links are:
Schema_links: [invoice_items.netamount,invoice_items.productid,invoice_items.description,invoice_header.creationdatetime,invoice_items.parentobjectid=invoice_header.objectid,1]
"""

no_product_schema = """
Q: "Show the revenues by customer for past year"
A: Let�~@~Ys think step by step. In the question "Show the revenues bycustomer for past year", we are asked:
"the revenue" so we need column = [invoice_header.totalnetamount]
"by customer" so we need column = [customercommon.businesspartnername,customer.objectid]
"for past year" so we need column = [invoice_header.creationdatetime]
Based on the columns and tables, we need these Foreign_keys = [customer.uuid=invoice_header.partyuuid,customercommon.parentobjectid=customer.objectid].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = [1]. So the Schema_links are:
Schema_links: [invoice_header.totalnetamount,customercommon.businesspartnername,customer.objectid,invoice_header.creationdatetime,customer.uuid=invoice_header.partyuuid,customercommon.parentobjectid=customer.objectid,1]
"""
schema_linking_prompt = """
Table Addresses, columns = [*,address_id,line_1,line_2,city,zip_postcode,state_province_county,country]
Table Candidate_Assessments, columns = [*,candidate_id,qualification,assessment_date,asessment_outcome_code]
Table Candidates, columns = [*,candidate_id,candidate_details]
Table Courses, columns = [*,course_id,course_name,course_description,other_details]
Table People, columns = [*,person_id,first_name,middle_name,last_name,cell_mobile_number,email_address,login_name,password]
Table People_Addresses, columns = [*,person_address_id,person_id,address_id,date_from,date_to]
Table Student_Course_Attendance, columns = [*,student_id,course_id,date_of_attendance]
Table Student_Course_Registrations, columns = [*,student_id,course_id,registration_date]
Table Students, columns = [*,student_id,student_details]
Foreign_keys = [Students.student_id = People.person_id,People_Addresses.address_id = Addresses.address_id,People_Addresses.person_id = People.person_id,Student_Course_Registrations.course_id = Courses.course_id,Student_Course_Registrations.student_id = Students.student_id,Student_Course_Attendance.student_id = Student_Course_Registrations.student_id,Student_Course_Attendance.course_id = Student_Course_Registrations.course_id,Candidates.candidate_id = People.person_id,Candidate_Assessments.candidate_id = Candidates.candidate_id]
Q: "List the id of students who never attends courses?"
A: Let’s think step by step. In the question "List the id of students who never attends courses?", we are asked:
"id of students" so we need column = [Students.student_id]
"never attends courses" so we need column = [Student_Course_Attendance.student_id]
Based on the columns and tables, we need these Foreign_keys = [Students.student_id = Student_Course_Attendance.student_id].
Based on the tables, columns, and Foreign_keys, The set of possible cell values are = []. So the Schema_links are:
Schema_links: [Students.student_id = Student_Course_Attendance.student_id]

Table invoice_items, columns = [*,parentobjectid,netamount,description,productid,partyuuid]
Table invoice_header, columns = [*,objectid,creationdatetime,totalnetamount]
Table customercommon, columns = [*,parentobjectid,businesspartnername]
Table customer, columns = [*,objectid,uuid]
Foreign_keys = [invoice_items.parentobjectid=invoice_header.objectid,customer.uuid=invoice_header.partyuuid,customercommon.parentobjectid=customer.objectid]
"""
PROMPT = PromptTemplate(
    input_variables=["input", "schema_links"],
    template=easy_template,
)

def format(sql):
    if "date" in sql:
        result = sql.replace("\'20", "TIMESTAMP \'20").replace("\"20", "TIMESTAMP \"20")
        return result
    else:
        return sql

def hive_search(sql):
    hive_host = ""
    port = 8080
    user_name = ""
    catalog=""
    hive_database = ""

    engine = create_engine(
        URL(
            host=hive_host,
            port=port,
            user=user_name,
            catalog=catalog,                                                                                                                                                                             schema=hive_database,
        ),
    )
    with engine.connect() as con:
        sql = format(sql)
        result_t = con.execute(text(sql))
        result = result_t.fetchall()
    return result


class DIN_Chain(Chain):
    """
    An example of a custom chain.
    """

    prompt: BasePromptTemplate
    """Prompt object to use."""
    llm: BaseLanguageModel
    output_key: str = "text"  #: :meta private:

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return self.prompt.input_variables[:1]

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(
            self,
            inputs: Dict[str, Any],
            run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        
        schema_links_prompt = schema_linking_prompt_maker(inputs.get("input"))
        schema_links = self.llm(schema_links_prompt)
        
        inputs["schema_links"] = schema_links
        if "by" in inputs.get("input"):
            self.prompt.template = hard_template
        else:
            self.prompt.template = easy_template
        prompt_value = self.prompt.format_prompt(**inputs)
        
        start = datetime.now()
        # Whenever you call a language model, or another chain, you should pass
        # a callback manager to it. This allows the inner run to be tracked by
        # any callbacks that are registered on the outer run.
        # You can always obtain a callback manager for this by calling
        # `run_manager.get_child()` as shown below.
        response = self.llm.generate_prompt(
            [prompt_value], callbacks=run_manager.get_child() if run_manager else None
        )
        #print(f'Original response:{response}')
        text = response.generations[0][0].text
        #pdb.set_trace()
        #print(f'Final Text:{text}')
        result_ = text.split("\n\n")[0]
        result_ = result_.replace("\n", " ")
        
        hive_result = hive_search(result_)
        if run_manager:
            run_manager.on_text("Log something about this run")

        return {self.output_key:hive_result}

    async def _acall(
            self,
            inputs: Dict[str, Any],
            run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        #print(f'DummyChain:{inputs}')
        # Your custom chain logic goes here
        # This is just an example that mimics LLMChain
        prompt_value = self.prompt.format_prompt(**inputs)

        # Whenever you call a language model, or another chain, you should pass
        # a callback manager to it. This allows the inner run to be tracked by
        # any callbacks that are registered on the outer run.
        # You can always obtain a callback manager for this by calling
        # `run_manager.get_child()` as shown below.
        response = await self.llm.agenerate_prompt(
            [prompt_value], callbacks=run_manager.get_child() if run_manager else None
        )

        # If you want to log something about this run, you can do so by calling
        # methods on the `run_manager`, as shown below. This will trigger any
        # callbacks that are registered for that event.
        if run_manager:
            await run_manager.on_text("Log something about this run")

        return {self.output_key: response.generations[0][0].text}

    @property
    def _chain_type(self) -> str:
        return "my_custom_chain"

def schema_linking_prompt_maker(test_sample_text):
    """
        use llm to create schema_links, schema_links is the sql column we need.
        for example: select id, name from class;
        schema_links:[class.id, class.name] 

        input: test_sample_text
        output: schema_links
    """
    instruction = "# Find the schema_links for generating SQL queries for each question based on the database schema and Foreign keys.\n"
    fields = """
    Table invoice_items, columns = [parentobjectid,netamount,description,productid,partyuuid]
    Table invoice_header, columns = [objectid,creationdatetime,totalnetamount]
    Table customercommon, columns = [parentobjectid,businesspartnername]
    Table customer, columns = [objectid,uuid,]
    """
    foreign_keys = """
    [invoice_items.parentobjectid=invoice_header.objectid,customer.uuid=invoice_header.partyuuid,customercommon.parentobjectid=customer.objectid]
    """
    global schema_linking_prompt
    if "product" in test_sample_text:
        schema_linking_prompt += product_schema
    else:
        schema_linking_prompt += no_product_schema
    prompt = instruction + schema_linking_prompt + fields +foreign_keys+ 'Q: "' + test_sample_text + """"\nA: Let’s think step by step."""
    return prompt

def get_din_chain(llm):
    chain = DIN_Chain(llm=llm, prompt=PROMPT)
    return chain


if __name__ == "__main__":
    chain = get_din_chain(llm)
    pdb.set_trace()
    query = "what are our revenues by product for the past 3 years"
    result = chain.run(query)
    print("query:", query)
    #print(result)

