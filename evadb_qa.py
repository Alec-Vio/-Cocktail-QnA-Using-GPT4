import os
from time import perf_counter

from gpt4all import GPT4All
from unidecode import unidecode
from util import download_cocktails, read_parsed_cocktails, process_cocktails
from openai import OpenAI

import evadb

def setup_context(cocktails_path: str):
    # Initialize early to exclude download time.
    # llm = GPT4All("ggml-model-gpt4all-falcon-q4_0.bin")

    client = OpenAI(api_key="")

    path = os.path.dirname(os.getcwd())
    cursor = evadb.connect().cursor()

    cocktail_table = "TablePPText"
    cocktail_feat_table = "FeatTablePPText"
    index_table = "IndexTable"

    timestamps = {}
    t_i = 0

    timestamps[t_i] = perf_counter()
    print("Setup Function")

    Text_feat_function_query = f"""CREATE FUNCTION IF NOT EXISTS SentenceFeatureExtractor
            IMPL  './sentence_feature_extractor.py';
            """

    cursor.query("DROP FUNCTION IF EXISTS SentenceFeatureExtractor;").execute()
    cursor.query(Text_feat_function_query).execute()

    cursor.query(f"DROP TABLE IF EXISTS {cocktail_table};").execute()
    cursor.query(f"DROP TABLE IF EXISTS {cocktail_feat_table};").execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Create table")

    cursor.query(f"CREATE TABLE {cocktail_table} (id INTEGER, data TEXT(1000));").execute()

    # Insert text chunk by chunk.
    # Prepare the SQL statement with placeholders
    for i, text in enumerate(read_parsed_cocktails(cocktails_path)):
        # Convert special characters
        ascii_text = unidecode(text)


        try:
            if ascii_text:
                cursor.query(f"""INSERT INTO {cocktail_table} (id, data) VALUES ({i}, '{ascii_text}');""").df()
        except Exception as e:
            print(f"Error inserting text at index {i}. Error message: {str(e)}")
            print(f"Failed text: {ascii_text[:50]}...")

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Extract features")

    # Extract features from text.
    cursor.query(
        f"""CREATE TABLE {cocktail_feat_table} AS
        SELECT SentenceFeatureExtractor(data), data FROM {cocktail_table};"""
    ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Create index")

    # Create search index on extracted features.
    cursor.query(
        f"CREATE INDEX {index_table} ON {cocktail_feat_table} (features) USING QDRANT;"
    ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")
    
    print("Query")
    ask_question("", "", cursor, cocktail_feat_table, client)

def ask_question(question, orig_quesiton, cursor, cocktail_feat_table, client):
    print("Ask Question")
    # Ask the actual question to the terminal
    hasRemade = True
    if question == "":
        whitelist = set(".!?:,abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        question = input("Please enter your question: ")
        question = ''.join(filter(lambda x: x in whitelist, question))
        orig_quesiton = question
        print(f"You asked: {question}")
        hasRemade = False

    # Make the question compatable with similarity
    ascii_question = unidecode(question)
    ascii_question = ascii_question.replace("'", "''")

    # Instead of passing all the information to the LLM, we extract the 10 topmost similar recipes
    # and use them as context for the LLM to answer.
    # We also set a threshold to avoid giving 10 unrelated recipes as context
    threshold = 1.2
    res_batch = cursor.query(
        f"""SELECT data, Similarity(SentenceFeatureExtractor('{ascii_question}'),features) FROM {cocktail_feat_table}
        WHERE Similarity(SentenceFeatureExtractor('{ascii_question}'),features) < {threshold}
        ORDER BY Similarity(SentenceFeatureExtractor('{ascii_question}'),features)
        LIMIT 10;"""
    ).execute()
    # res_batch = cursor.query(
    #     f"""SELECT data FROM {cocktail_feat_table}
    #     ORDER BY Similarity(SentenceFeatureExtractor('{ascii_question}'),features)
    #     LIMIT 5;"""
    # ).execute()

    context_list = []
    context_list.append("Context:\n")
    if (len(res_batch ) == 0 and not hasRemade):
        remakeQuestion(question, client, cursor, cocktail_feat_table)
        

    for i in range(len(res_batch)):
        context_list.append(res_batch.frames[f"{cocktail_feat_table.lower()}.data"][i])

    considerContextQuality(context_list, question, orig_quesiton, client, hasRemade, cursor, cocktail_feat_table)

def inventRecipe(question, client, cursor, cocktail_feat_table):
    print("Inventing a Recipe")
    query = ["\nQuestion:\n" + question + "\n"]
    query.append("The above question is a user trying to find a good recipe for a cocktail based on what they feel like drinking at the moment."
                 + "\nPlease invent a cocktail that would match what the user is trying to get based on their question."
                 + "\nUSE THE FOLLOWING FORMAT FOR THE COCKTAIL:"
                 + "\nTitle: ingredient: ingredient: ...: ingredient: instructions on drink assembly"
                 + "\nHere's an example:"
                 + "\nABC: 2oz amaretto: 2oz baileys Irish cream: 2oz cointreau: assemble in a lowball glass and stir"
                 + "\nSo it's a title, list of ingredients, and instructions all in a colon separated list on ONE SINGULAR LINE AT THE BEGINNING OF THE RESPONSE"
                 + "\nTHE FORMAT OF YOUR RESPONSE IS ONE COCKTAIL IN THE FORMAT ABOVE. AFTER WRITING THE RECIPE (WHICH IS ALL JUST ONE LONG STRING),"
                 + " CREATE A NEW LINE AND JUSTIFY THE COCKTAIL")
    query = "\n".join(query)
    
    full_response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=query,
        max_tokens=500
    )

    full_response_text = full_response.choices[0].text.strip()
    print("\n" + full_response_text)

    question = input("Do you want to add this recipe to the database? (YES/NO): ")
    if question.lower() == "yes":
        whitelist = set(".!?:,abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        recipe = full_response_text.split("\n", 1)[0]

        filtered_recipe = ''.join(filter(lambda x: x in whitelist, recipe))
        with open("cocktails_list.txt", "a") as file:
            file.write(filtered_recipe + "\n")
        print("Recipe added to the database.")
    else:
        question = input("Do you want to ask another question? (YES/NO): ")
        if question.lower() == "yes":
            ask_question("", "", cursor, cocktail_feat_table, client)
    return True

def remakeQuestion(question, client, cursor, cocktail_feat_table):
    print("Remaking Question")
    query = ["\nQuestion:\n" + question + "\n"]
    query.append("The above question is a user trying to find a good recipe for a cocktail based on what they feel like drinking at the moment."
                 + "\nThe way the question is used is that it is put into a similarity function that compares it to a vectorized database of cocktail"
                 + " recipes that are composed of a title, list of ingredients, and instructions to make the drink."
                 + "\nThis particular question has been run through the similarity function and produces poor results, as in the drinks that have the"
                 + " highest similarity score have nothing to do with what the question wants."
                 + "\nPlease come up with a question to be compared to the recipes in a similarity function that will result in more relevant results."
                 + "\nThat could include more relevent words or phrases that match the question like a list of ingredients that would be in a drink that"
                 + " is being asked for or anythig like that."
                 + "\FORMAT OF YOUR RESPONSE:"
                 + "\ONE SHORT SENTENCE OR LIST OR MESSAGE THAT, WHEN COMPARED IN A SIMILARITY FUNCTION WITH THE RECIPE DATABASE, WILL RESULT IN DRINKS"
                 + " THAT MATCH THE WANTS OF THE ORIGINAL QUESTION."
                 + "\nONLY PROVIDE THE SHORT MESSAGE THAT WILL BE COMPARED AND NOTHING ELSE")
    query = "\n".join(query)
    
    full_response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=query,
        max_tokens=500
    )
    print("The new question is: ", full_response.choices[0].text.strip())

    ask_question(full_response.choices[0].text.strip(), question, cursor, cocktail_feat_table, client)
    return True

def considerContextQuality(context, question, orig_quesiton, client, hasRemade, cursor, cocktail_feat_table):
    print("Considering Quality")
    # context.append("\nQuestion:\n" + question + "\n")
    query = []
    query.append("Below is a context filled with cocktail recipes from a database and a question"
                   + "\nThe recipes are in the format of title, then list of ingredients, then instructions, all colon seperated."
                   + "\nThe question is what the user was trying to get out of the database and the context is the result of "
                   + " running that question through a similarity function with a vectorized version of the cocktail database."
                   + "\nDo the cocktails in the context properly represent the type of thing the question is asking for, as in "
                   + " does the context deliver on what the question being asked."
                   + "\nPLEASE ONLY RESPOND WITH ONE WORD, YES OR NO. YES, MEANING THE CONTEXT IS GOOD AND NO MEANING THE CONTEXT IS BAD")
    for i in range(len(context)):
        query.append(context[i])
    query.append("\nQuestion:\n" + orig_quesiton + "\n")
    query = "\n".join(query)

    full_response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=query,
        max_tokens=500
    )
    if full_response.choices[0].text.strip().lower() =="yes":
        llm_qna(context, orig_quesiton, client, cursor, cocktail_feat_table)
    elif (hasRemade):
        inventRecipe(orig_quesiton, client, cursor, cocktail_feat_table)
    else:
        remakeQuestion(question, client, cursor, cocktail_feat_table)
    return True

def llm_qna(context, question, client, cursor, cocktail_feat_table):
    print("Getting Your Results")
    query = []
    query.append("The above context is a list of cocktail recipes taken from a larger database of recipes."
                   + "\nThe recipes are in the format of title, then list of ingredients, then instructions, all colon seperated."
                   + "\nThe question is what the user was trying to get out the context."
                   + "\nPlease use the list of cocktails in the context to provide an answer to the question."
                   + "\n\nRULES OF YOUR RESPONSE:"
                   + "\nYOU WILL LIST EXACTLY ONE RECIPE AND YOU WILL LIST IT IN THE COLON SEPERATED FORMAT OF THE RECIPES IN THE CONTEXT"
                   + "\nTHE BEGINNING OF YOUR RESPONSE WILL JUST BE THE RECIPE, FOLLOWED BY A SEMICOLON AND THEN YOUR JUSTIFICATION")
    for i in range(len(context)):
        query.append(context[i])
    query.append("\nQuestion:\n" + question + "\n")
    query = "\n".join(query)
    
    full_response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=query,
        max_tokens=500
    )
    print(full_response.choices[0].text.strip())

    followup = input("\n\nDo you have any followup questions about this drink? (YES/NO): ")
    while followup.lower() == "yes":
        whitelist = set(".!?:,abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        question = input("What's your question?: ")
        question = ''.join(filter(lambda x: x in whitelist, question))
        cocktail = full_response.choices[0].text.strip().split(":", 1)[0]
        query = ("The topic of conversation is a cocktail called " 
        + cocktail
        + "\nQuestion:\n"
        + question)
        full_response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=query,
            max_tokens=500
        )
        print("\n" + full_response.choices[0].text.strip())
        followup = input("\nDo you have any followup questions about this drink? (YES/NO): ")

    question = input("Do you want to ask another question? (YES/NO): ")
    if question.lower() == "yes":
        ask_question("", "", cursor, cocktail_feat_table, client)

    return True

def main():
    orig_path = download_cocktails()
    parsed_path = process_cocktails(orig_path)

    setup_context(parsed_path)


if __name__ == "__main__":
    main()