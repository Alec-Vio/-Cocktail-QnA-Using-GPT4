# Cocktail Question and Answering
This program demonstrates the capability of EvaDB in extracting embedding from texts, building similarity index, and using **OpenAI gpt-3.5-turbo-instruct LLM** to answer question based on that. For this example, we use a .txt file full of various cocktail recipes in a consistent format as the source for our demonstration purpose.

This app is powered by EvaDB and OpenAI. An OpenAI API Key is necessary.

## How it works
The program uses a small context of cocktail recipes that are extracted from a .txt file and handed to an LLM to use and answer questions

### setup_context
The program first initializes an OpenAI instance with your API Key and sets up EvaDB for query creation later on. Several tables are created to first add the contents of the data file to it, another to have every recipe in the file vectorized, and a final one to index the entire table. All this is so that a similarity function can be run later on the data.

### ask_question
This function is called immediately after setup and is rerun if a new question has to be created. The function asks the terminal for a question to the mixologist if there is not a question already, vectorizes the question, and runs an EvaDBs similarity function on it and the table of cocktail recipes to find the 10 recipes that fit the question best, provided that they within a set similarity to the question. The list is then added to an array for further use.

### consider_context_quality
This function takes in the context from the similarity function run and combines it and the question asked into a query with an included message to get the LLM to make sure that the context provided relevant drinks to the question and, when the LLM is called, it will respond with either a YES or a NO. If it's a yes, it will move on to llm_qna and if it's a no, it will go to remake_question. If it's already had to do that, it will go to invent_recipe.

### llm_qna
This function is for when it is confirmed that the context and the question are relevant to one another and that there is a solid answer to the question available. The function creates a query with the context, the question, and a message informing the LLM on how to answer the question using the context. The LLM receives the query and gives an answer of one of the recipes. The terminal user is then prompted to say whether they want to ask any follow-up questions and if it receives a yes, a prompt to ask a question of the LLM. If it is asked a follow-up question, it will use the name of the cocktail it recommended as context and then answer the question with that cocktail in mind. It will continue to ask for follow-up questions until it receives something other than a no. At that point, it will ask if you want to ask about more cocktails, and if it receives a yes it sends you back to ask_question.

### remake_question
This function takes in the original question and, using an LLM creates a new question to be used by the similarity function to hopefully have more success in retrieving recipes relevant to the original question.

### invent_recipe
This function takes in the original question and, using an LLM invents a completely new cocktail recipe according to the description of the question. Once it creates a recipe, it will ask if the user wants it to be added to the database, and if the user says yes, it will format the recipe correctly for the data file and add it to the back of the file.

## Setup
Ensure that the local Python version is >= 3.8. Install the required libraries:

```bat
pip install -r requirements.txt
```

### How to Run
```bash
python evadb_qa.py
```

## 
