import gradio as gr
import sqlite3
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY") # getting the API Key

# Initializing the llama3-8b-8192 model from Groq
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    verbose=True,
    api_key=GROQ_API_KEY
)


query_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
            You are an SQL and data analysis expert. Generate an appropriate SQL query using SQLite syntax for the question provided, without any explanations or code comments.
            Follow SQLite-specific conventions, as shown in the examples below:
            
            Example 1:
            Question: "What is the average fare for trips over 10 miles?"
            SQL Query: SELECT AVG(fare_amount) FROM taxi_data WHERE trip_distance > 10;

            Example 2:
            Question: "How many trips were taken in each month?"
            SQL Query: SELECT strftime('%m', pickup_datetime) AS month, COUNT(*) AS trip_count FROM taxi_data GROUP BY month;

            Example 3:
            Question: "What is the total fare amount for each driver (medallion) per day?"
            SQL Query: SELECT DATE(pickup_datetime) AS date, medallion, SUM(fare_amount) AS total_fare FROM taxi_data GROUP BY date, medallion;
            
            SQLite-Specific Conventions:
            
            1. Date and Time Extraction:
               - Instead of `EXTRACT(YEAR FROM column)`, use `strftime('%Y', column)` to extract the year.
               - Example: `SELECT strftime('%Y', pickup_datetime) FROM taxi_data;`

            2. String Length:
               - Instead of `CHAR_LENGTH(column)`, use `LENGTH(column)`.
               - Example: `SELECT LENGTH(passenger_name) FROM taxi_data;`

            3. Regular Expressions:
               - SQLite does not support `REGEXP`. Use `LIKE` for simple patterns or avoid regular expressions.
               - Example: `SELECT * FROM taxi_data WHERE passenger_name LIKE 'A%';`

            4. Window Functions:
               - For row numbering, use `ROW_NUMBER()` if supported, or simulate with joins.
               - Example: `SELECT id, ROW_NUMBER() OVER (ORDER BY pickup_datetime) AS row_num FROM taxi_data;`

            5. Data Type Casting:
               - Use `CAST(column AS TYPE)`, but note that SQLite supports limited types.
               - Example: `SELECT CAST(fare_amount AS INTEGER) FROM taxi_data;`

            6. Full Outer Join Workaround:
               - SQLite doesn’t support `FULL OUTER JOIN`. Combine `LEFT JOIN` and `UNION` for a similar effect.
               - Example:
                 ```
                 SELECT a.*, b.*
                 FROM table_a a
                 LEFT JOIN table_b b ON a.id = b.id
                 UNION
                 SELECT a.*, b.*
                 FROM table_a a
                 RIGHT JOIN table_b b ON a.id = b.id;
                 ```

            Use these examples and guidelines to generate an SQL query compatible with SQLite syntax for the question provided.
        """),
        ("human", "{question}"),
    ]
)
interpret_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an experienced data analyst. Provide a concise, natural language answer based on the given data summary. If relevant, give key statistics, trends, or patterns."),
        ("human", "{question} Data Summary:\n{data_summary}")
    ]
)


def ask_question(question, file):
    conn = sqlite3.connect(':memory:') # connecting to sqlite database
    cur = conn.cursor() # creating a cursor object


    df = pd.read_csv(file.name) # loading the csv file to database
    df.to_sql('data_tab', conn, if_exists='replace', index=False)


    cur.execute("PRAGMA table_info(data_tab);")     # getting the column names to give the LLM some context
    clmns = [info[1] for info in cur.fetchall()]
    clmns_str = ", ".join(clmns)


    question_with_context = f"The table 'data_tab' has columns: {clmns_str}. {question}" # a template for asking LLM a question with come context 
    ai_msg = query_prompt | llm  # the chain, asking the question and getting the response from LLM
    sql_query = ai_msg.invoke({"question": question_with_context}).content.strip()


    print(f"The generated SQL Query:{sql_query}")  # printing the query just for debugging purposes locally

    try:
        result_df = pd.read_sql_query(sql_query, conn)
        dt_sumry = result_df.describe(include='all').to_string() if not result_df.empty else "No relevant data found."

        
        answer_chain = interpret_prompt | llm  # a chain to interpret the response from LLM i.e. the data 
        final_answer = answer_chain.invoke({"question": question, "data_summary": dt_sumry}).content.strip()

        conn.close()  # closing the connection

        return f"Generated SQL Query:\n{sql_query}\nAnswer:\n{final_answer}"

    except Exception as e:
        conn.close()
        return f"Error executing query: {e}"




with gr.Blocks() as demo: # the Gradio Interface
    file_input = gr.File(label="Upload a CSV file")
    question_input = gr.Textbox(label="Ask a question about your data")
    output = gr.Textbox(label="Answer")

    submit_button = gr.Button("Submit")
    submit_button.click(fn=ask_question, inputs=[question_input, file_input], outputs=output)
    
    gr.Markdown("""
    ### Instructions:
    1. Upload a CSV file containing the data you want to analyze.
    2. Type a question about the data in the text box provided.
    3. Click 'Submit' to receive an SQL query and the corresponding answer.
    4. Make sure that your CSV file is not too large
    """)

demo.launch()




