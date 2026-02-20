from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model=genai.GenerativeModel("gemini-2.5-flash")

def my_output(query):
    response=model.generate_content(query)
    return response.text

#for UI
st.set_page_config(page_title="QUERY_BOT")
st.header("QUERY_BOT")
input=st.text_input("input",key='input')
submit=st.button("Ask your query:")

if submit:
    response=my_output(input)
    st.subheader("The Response is :")
    st.write(response)