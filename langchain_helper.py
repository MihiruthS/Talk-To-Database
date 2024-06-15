from langchain import OpenAI
import os
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import SemanticSimilarityExampleSelector
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX,_mysql_prompt
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import  FewShotPromptTemplate
from secret_key import openai_key
from few_shots import few_shots


os.environ['OPENAI_API_KEY'] = openai_key
llm = OpenAI(temperature = 0.1)

def get_few_shot_db_chain():
    db_user = "root"
    db_password = "1216Mihi#"
    db_host = "127.0.0.1"
    db_name = "atliq_tshirts"

    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",sample_rows_in_table_info = 4)

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-V2')
    to_vectorize = [f"{item['Question']} {item['SQLQuery']} {item['SQLResult']} {item['Answer']}" for item in few_shots]
    vectorstore = Chroma.from_texts(to_vectorize, embedding=embeddings, metadatas=few_shots)
    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2,
    )

    example_selector.select_examples({"Question": "How many Adidas T shirts I have left in my store"})

    example_prompt = PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult", "Answer", ],
        template="\nQuestion:{Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}"
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=_mysql_prompt,
        suffix=PROMPT_SUFFIX,
        input_variables=["input", "table_info", "top_k"],
    )

    chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, prompt=few_shot_prompt)
    return chain

if __name__ == "__main__":
    chain = get_few_shot_db_chain()
    print(chain.run("How many white color Levi's t shirts do we have"))


