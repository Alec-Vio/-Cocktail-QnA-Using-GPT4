# coding=utf-8
# Copyright 2018-2023 EvaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import urllib.request
import re

def download_cocktails():
    orig_file_path = "cocktails.txt"
    
    if not os.path.exists(orig_file_path):
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/verdammelt/defdrink/master/drinks.txt", orig_file_path
        )
        
    return orig_file_path

def process_cocktails(orig_file_path):
    parsed_file_path = "parsed_cocktails.txt"

    with open(parsed_file_path, "w", encoding='utf-8') as new_f:
        with open(orig_file_path, "r", encoding='utf-8') as f:
            cocktails = re.split(r'\-{39,}', f.read())
            
            for cocktail in cocktails:
                lines = cocktail.strip().split("\n")
                clean_lines = []
                
                for line in lines:
                    splits = line.split("|")
                    num_bars = line.count("|")
                    
                    # Adjust the entries based on the count of '|' characters
                    if num_bars == 1:
                        splits = [splits[0], splits[1]]
                    elif num_bars == 2:
                        splits = [splits[0], splits[1], splits[2]]
                    
                    for index, split_item in enumerate(splits):
                        split_item = split_item.strip().lower()
                        # If there's a previous line (title) for this index, append to it; otherwise, start a new line
                        if len(clean_lines) > index and clean_lines[index].startswith("** "):
                            clean_lines[index] += (":" if split_item else "") + split_item
                        else:
                            # In case there's no title, we make one from the previous title.
                            clean_lines.append(split_item if split_item else "")


                # Write to the parsed file
                for line in clean_lines:
                    if line and not line.startswith("** "):  # Skip empty lines and titles
                        new_f.write(":" + line)
                    elif line.startswith("** "):
                        new_f.write("\n" + line + " ")
                new_f.write("")
                
    return parsed_file_path


def read_parsed_cocktails(path, num_token = 1000):

# For simplicity, we only keep letters.
    whitelist = set(".!?:,abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

    with open(path, "r") as f:
        line_itr = 0
        for line in f.readlines():
            line_itr = line_itr + 1
            if line_itr % 10 == 0:
                print("line: " + str(line_itr))
            for i in range(0, len(line), num_token):
                cut_line = line[i : min(i + 1000, len(line))]
                cut_line = "".join(filter(whitelist.__contains__, cut_line))
                yield cut_line

            if line_itr == 1000:
                break


def try_execute(conn, query):
    try:
        conn.query(query).execute()
    except Exception:
        pass