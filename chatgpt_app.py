# Import required packages
import streamlit as st
import openai

# Set the model engine and your OpenAI API key
model_engine = "text-davinci-003"
openai.api_key = "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"

st.title("Chatting with ChatGPT")
st.sidebar.header("Instructions")
st.sidebar.info(
    '''This is a web application that allows you to interact with 
       the OpenAI API's implementation of the ChatGPT model.
       Enter a **query** in the **text box** and **press enter** to receive 
       a **response** from the ChatGPT
       '''
)

def ChatGPT(user_query):
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=user_query,
        max_tokens=1024,
        n=1,
        temperature=0.5,
    )
    response = completion.choices[0].text
    return response

def main():
    user_query = st.text_input("Enter query here, to exit enter :q", "what is Python?")
    if user_query != ":q" or user_query != "":
        response = ChatGPT(user_query)
        st.write(f"{user_query} {response}")

main()