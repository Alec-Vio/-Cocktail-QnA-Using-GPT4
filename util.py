import os
import urllib.request
import re

def download_cocktails():
    orig_file_path = "cocktails_list.txt"
    
    if not os.path.exists(orig_file_path):
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/verdammelt/defdrink/master/drinks.txt", orig_file_path
        )
        
    return orig_file_path

def process_cocktails(orig_file_path):
    parsed_file_path = "parsed_cocktails.txt"
    whitelist = set(".!?:,abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

    with open(parsed_file_path, "w", encoding='utf-8') as new_f:
        with open(orig_file_path, "r", encoding='utf-8') as f:
            for line in f:
                clean_line = "".join(filter(whitelist.__contains__, line))
                new_f.write(clean_line + "\n")  # Add a line break after each line
                
    return parsed_file_path


def read_parsed_cocktails(path):

    # Open and read the file
    with open(path, "r") as f:
        for line in f:
            # Yield the line
            yield line


def try_execute(conn, query):
    try:
        conn.query(query).execute()
    except Exception:
        pass