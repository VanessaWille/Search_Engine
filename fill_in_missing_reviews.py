import pandas as pd
import os
import json
from Ollama_connection import OllamaConnection
from dotenv import load_dotenv
import time

REVIEWS_CHECKPOINT_PATH = "reviews/checkpoints/missing_reviews_bank_checkpoint.xlsx"
LLM_GRADES_PATH = "reviews/checkpoints/llm_grades.xlsx"
MISSING_REVIEWS_BANK_PATH  = "reviews/missing_reviews_bank.xlsx"
KEY_COLUMNS = ["Tipo", "Descrição", "Query", "id", "title"]
PROMPT_ENDING = "\n\nYour answer should be only a block of code in json format, with the 'Assistant grading' key containing the integer format grade and the 'Justificative' key containing the justificative."
EVALUATOR = "llama"
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
if not OLLAMA_HOST:
    raise Exception('OLLAMA_HOST não está definida')
ollama_connection = OllamaConnection("llama3", OLLAMA_HOST)

def fill_in_missing_reviews():
    prompt_ending = PROMPT_ENDING

    # if the checkpoint does not exist, we will get the missing reviews from the missing reviews bank
    if not os.path.exists(REVIEWS_CHECKPOINT_PATH):
        missing_grades_df = get_to_be_graded_reviews()
        missing_grades_df["llm_response"] = None
    else:
        missing_grades_df = pd.read_excel(REVIEWS_CHECKPOINT_PATH)

    # get the llm responses for the missing reviews
    for index, row in missing_grades_df.iterrows():
        if row["llm_response"] is None:
            prompt = row["gpt_template"] + prompt_ending
            response = ollama_connection.ask_the_llm(prompt)
            missing_grades_df.at[index, "llm_response"] = response
            missing_grades_df.to_excel(REVIEWS_CHECKPOINT_PATH, index=False)
    
    # now we get the grades from the llm responses
    graded_by_llm = get_grades_from_llm_responses(missing_grades_df)
    # now we save the new llm reviews
    save_new_llm_reviews(graded_by_llm)

    # now we add the new grades to the missing reviews bank
    missing_reviews_bank = load_missing_reviews_bank()
    missing_reviews_bank = fill_graded_reviews_from_checkpoint(missing_reviews_bank, graded_by_llm)

    # now we save the new missing reviews bank
    save_new_reviews(missing_reviews_bank)

    # we will delete the checkpoint
    save_new_llm_reviews(None)
    if os.path.exists(REVIEWS_CHECKPOINT_PATH):
        os.remove(REVIEWS_CHECKPOINT_PATH)

def get_grades_from_llm_responses(df):
    df["Justificativa"] = None

    for index, row in df.iterrows():
        response = row["llm_response"]
        response = fix_llm_response(response)
        # this is supposed to be a json response, lets check if it is a valid json
        if response:
            data = json.loads(response)
            grade = data["Assistant grading"]
            justificative = data["Justificative"]
            df.at[index, "Nota"] = grade
            df.at[index, "Justificativa"] = justificative
            df["Evaluator"] = EVALUATOR
        
    return df

def fix_llm_response(response):
    if not type(response) == str:
        return None

    # if the response is not a valid json, we will try to fix it
    if not valid_json(response):
        # the response is not a valid json, we will try to fix it
        # we will find whats after the last { and before the first } in the after part
        response = "{" + response.split("{")[-1].split("}")[0] + "}"
    
    if not valid_json(response):
        print("could not fix the response: ", response)
        # possible more fixes here ...

    if not valid_json(response):
        # if the response is still not a valid json, we will return None
        return None
    else:
        return response
    
def valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except:
        return False
    
def load_missing_reviews_bank():
    missing_reviews_bank = pd.read_excel(MISSING_REVIEWS_BANK_PATH)
    return missing_reviews_bank

def split_reviewed_and_missing(df):
    df_not_graded = df[df["Nota"].isna()] # only get the reviews that have not been graded yet
    df_graded = df[~df["Nota"].isna()] # only get the reviews that have been graded
    return df_not_graded, df_graded

def load_new_llm_reviews():
    path = LLM_GRADES_PATH
    try:
        df = pd.read_excel(path)
    except:
        df = None
    return df

def save_new_llm_reviews(df):
    path = LLM_GRADES_PATH
    if df is not None:
        df.to_excel(path, index=False)
    else:
        # if the df is None, we will delete the file
        try:
            os.remove(path)
        except:
            # if the file does not exist there is no check point to delete
            pass

def get_to_be_graded_reviews():
    # the first step is to get the missing reviews
    missing_reviews_bank = load_missing_reviews_bank()
    # now we get the new llm reviews
    review_checkpoint = load_new_llm_reviews()

    # if the checkpoint is empty, we will fill the missing reviews
    if review_checkpoint is None:
        missing_reviews_bank_not_graded, missing_reviews_bank_graded = split_reviewed_and_missing(missing_reviews_bank)
        return missing_reviews_bank_not_graded
    else:
        # if the checkpoint is not empty, we will get the reviews that have been graded and the ones that have not been graded
        review_checkpoint_not_graded, review_checkpoint_graded = split_reviewed_and_missing(review_checkpoint)
        # now we will overwrite in the missing reviews bank the reviews that have been graded from the checkpoint
        missing_reviews_bank = fill_graded_reviews_from_checkpoint(missing_reviews_bank, review_checkpoint_graded)
        # now lets save the new missing reviews bank and delete the checkpoint
        save_new_reviews(missing_reviews_bank)
        save_new_llm_reviews(None)

        return review_checkpoint_not_graded

def fill_graded_reviews_from_checkpoint(base_reviews, graded_reviews):
    # split the graded and not graded reviews
    base_reviews_not_graded, base_reviews_graded = split_reviewed_and_missing(base_reviews)

    # add the graded_reviews to the base_reviews_not_graded
    graded_reviews = graded_reviews[KEY_COLUMNS+["body", "Nota", "Evaluator", "Justificativa"]]
    base_reviews_not_graded = pd.concat([base_reviews_not_graded, graded_reviews])
    # now we have some keys with both a graded and a not graded review
    # we will keep the graded review
    base_reviews_not_graded = base_reviews_not_graded.drop_duplicates(subset=KEY_COLUMNS, keep="last")
    # now we will concatenate the graded reviews with the not graded reviews
    base_reviews = pd.concat([base_reviews_not_graded, base_reviews_graded])
    return base_reviews

def save_new_reviews(df):
    # save the new reviews
    df.to_excel(MISSING_REVIEWS_BANK_PATH, index=False)

if __name__ == "__main__":
    start_time = time.time()
    fill_in_missing_reviews()
    end_time = time.time()
    print("Done! - Time taken: ", round(end_time - start_time, 2), "seconds")