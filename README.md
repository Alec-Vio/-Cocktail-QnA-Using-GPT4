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
This function takes in the original question and, using an LLM creates a new question to be used by the similarity function to hopefully have more success in retrieving recipes relevant to the original question. It then calls the ask_question function using the generated question.

### invent_recipe
This function takes in the original question and, using an LLM invents a completely new cocktail recipe according to the description of the question. Once it creates a recipe, it will ask if the user wants it to be added to the database, and if the user says yes, it will format the recipe correctly for the data file and add it to the back of the file.

### Basic run-through
1. Setup context
2. Ask the user for a question
3. Find relevant recipes for the question using a similarity function
4. Check quality of the recipes in relation to the question
5. The recipes are irrelevant\n
   - Create a new question and take that back to step 3
   -  ...or if the question has already been made
      - Invent a recipe based on the original question
      - Ask the user if the recipe should be added to the database
      - If yes, format and add the question to the database
6. Get the LLM to generate the best recipe from the context for the question
7. Ask the user if they want a follow-up question about the recipe
8. If yes, continue to answer follow-up questions based on the recommended recipe
9. Ask the user if they want to ask another question for a recipe
10. If yes, return to step 2

## Setup
Ensure that the local Python version is >= 3.8. Install the required libraries:

```bat
pip install -r requirements.txt
```

### How to Run
```bash
python evadb_qa.py
```

## Examples
Here are some runs of the program. The format will be all the terminals from the run of the program copied and pasted here. Anytime there is a question or a prompt and then writing afterward, that is the program prompting for terminal input and then the writing afterward is the input given by me, the user.

### Example One
In this one, all functions are utilized. First, the question makes it all the way to the llm_qna and answers a follow-up question well. Then, when another cocktail question is asked, the context creation is not good enough and the question is remade, which also creates a failed context and a recipe is invented and added to the database.
```
Setup Function
Time: 2382.279 ms
Create table
Time: 3638.737 ms
Extract features
Time: 2092.325 ms
Create index
Time: 1148.241 ms
Ask Question
Please enter your question: Recommend me a strong drink
You asked: Recommend me a strong drink
Query
Time: 2139.010 ms
Considering Quality
Time: 597.564 ms
Getting Your Results
White Lady: 2 oz gin: 12 oz Cointreau: 12 oz lemon juice: shake all ingredients with ice, strain into a cocktail glass
; White Lady is a strong drink that contains 24 oz of alcohol with only 12 oz of mixers and no additional liquid ingredients.
Time: 887.903 ms


Do you have any followup questions about this drink? (YES/NO): Yes
What's your question?: can I substitute the gin for something?

Yes, you can substitute the gin with vodka or even a white tequila. Some people also like to use triple sec or Cointreau as a gin alternative in a White Lady cocktail.

Do you have any followup questions about this drink? (YES/NO): no
Do you want to ask another question? (YES/NO): yes
Ask Question
Please enter your question: recommend me another strong drink
You asked: recommend me another strong drink
Query
Time: 2252.826 ms
Considering Quality
Time: 444.985 ms
Remaking Question
The new question is: "Recommend me a vodka-based drink with pineapple juice and coconut rum."
Time: 511.932 ms
Ask Question
Query
Time: 2611.810 ms
Considering Quality
Time: 215.327 ms
Inventing a Recipe

Spiced Moscow Mule: 2oz vodka: 1oz lime juice: 1oz honey syrup: 2oz ginger beer: dash of bitters: garnish with lime wedges and fresh rosemary: in a mule mug, muddle lime wedges with honey syrup and bitters, add vodka and lime juice, fill with ice, top with ginger beer, stir and garnish.

This cocktail would be a great recommendation for the user as it has a mix of strong and refreshing flavors. The combination of vodka, lime juice, and ginger beer creates a balanced and tangy base, while the addition of honey syrup and bitters adds a touch of sweetness and depth. The lime wedges and rosemary not only add a pop of color but also enhance the aroma of the drink. Overall, the Spiced Moscow Mule is a perfect blend of strong and flavorful ingredients, making it a great choice for those looking for a strong drink.
Do you want to add this recipe to the database? (YES/NO): yes
Recipe added to the database.
Time: 44252.736 ms
```

## Example 2
In this example, the remaking of a question has to happen and is successful in creating a good context, which is then used in the llm_qna.
```
Setup Function
Time: 2269.072 ms
Create table
Time: 3398.215 ms
Extract features
Time: 2025.123 ms
Create index
Time: 1104.044 ms
Ask Question
Please enter your question: recommend me a weird cocktail
You asked: recommend me a weird cocktail
Query
Time: 2777.263 ms
Considering Quality
Time: 323.408 ms
Remaking Question
The new question is:  "Weird cocktail with gin and citrus."
Time: 378.330 ms
Ask Question
Query
Time: 2682.286 ms
Considering Quality
Time: 225.926 ms
Getting Your Results
Electric Kool-Aid: 1.5oz vodka: 1oz blue curacao: 1.5oz cranberry juice: 1oz lime juice: assemble in a highball glass filled with ice and stir 

This cocktail has a bright blue color similar to Kool-Aid, giving it a playful and fun appearance. The combination of vodka, blue curacao, cranberry juice, and lime juice creates a unique and refreshing flavor that is sure to surprise the taste buds. The name "Electric Kool-Aid" also adds to the overall quirkiness and weirdness of this cocktail, making it a perfect choice for someone looking for an unconventional drink experience.
Time: 918.612 ms


Do you have any followup questions about this drink? (YES/NO): no
Do you want to ask another question? (YES/NO): no
Time: 15430.556 ms
```
