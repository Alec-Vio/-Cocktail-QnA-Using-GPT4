import os
from time import perf_counter

from gpt4all import GPT4All
from unidecode import unidecode
from util import download_cocktails, read_parsed_cocktails, process_cocktails

import evadb


def ask_question(story_path: str):
    # Initialize early to exclude download time.
    llm = GPT4All("ggml-model-gpt4all-falcon-q4_0.bin")

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
    for i, text in enumerate(read_parsed_cocktails(story_path)):
        # Convert special characters
        ascii_text = unidecode(text)


        try:
            if ascii_text:
                cursor.query(f"""INSERT INTO {cocktail_table} (id, data) VALUES ({i}, '{ascii_text}');""").df()
                # print(ascii_text)
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

    # Search similar text as the asked question.
    question = "Recommend me a strong drink"
    ascii_question = unidecode(question)

    # Instead of passing all the information to the LLM, we extract the 5 topmost similar sentences
    # and use them as context for the LLM to answer.
    ascii_question = ascii_question.replace("'", "''")
    res_batch = cursor.query(
        f"""SELECT data FROM {cocktail_feat_table}
        ORDER BY Similarity(SentenceFeatureExtractor('{ascii_question}'),features)
        LIMIT 5;"""
    ).execute()

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("Merge")

    # Merge all context information.
    context_list = []
    context_list.append("""The items below are recipes for cocktails.
    The format is Name of Cocktail followed by ingredients in it and steps to make it, all seperated by colons\n
    You should try to answer the question using the given cocktails below, even if they're not a direct match. 
    If it is unreasonable use the given cocktails, then please make up your own""")
    for i in range(len(res_batch)):
        context_list.append(res_batch.frames[f"{cocktail_feat_table.lower()}.data"][i])
    context = "\n".join(context_list)

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print("LLM")

    # LLM
    query = f"""
    
    {context}
    
    Question : {question}"""
    print(query)

    full_response = llm.generate(query)

    print("Response" + full_response)

    t_i = t_i + 1
    timestamps[t_i] = perf_counter()
    print(f"Time: {(timestamps[t_i] - timestamps[t_i - 1]) * 1000:.3f} ms")

    print(f"Total Time: {(timestamps[t_i] - timestamps[0]) * 1000:.3f} ms")


def main():
    orig_path = download_cocktails()
    parsed_path = process_cocktails(orig_path)

    ask_question(parsed_path)


if __name__ == "__main__":
    main()