"""
This code is responsible for turning the csvs into a folder system or dataset that can be used by the model.
"""

import os
import pandas as pd
import shutil
import numpy as np
import random
import tqdm

def recipe_file_body(recipe, reviews):
    """
    Function responsible for creating the recipe body.
    """
    # getting the average rating
    avg_rating = reviews['rating'].mean()

    # if the average rating is NaN, we will set it to "No reviews"
    if np.isnan(avg_rating):
        avg_rating = "No reviews"

    # creating the recipe body
    recipe_body = recipe['name'] + '\n\n' \
    + "Recipe posted on: " + str(recipe['submitted']) + '\n\n' \
    + "Tags: " + ', '.join(recipe['tags']) + '\n\n' \
    + "Description: " + recipe['description'] + '\n\n' \
    + "This recipe takes " + str(recipe['minutes']) + " minutes to be done." + '\n\n' \
    + "For this recipe you will need the ingredients: " + '\n' \
    + '\n'.join(recipe['ingredients']) + '\n\n' \
    + "The "+str(recipe["n_steps"])+" steps to make this recipe are: " + '\n' \
    + '\n'.join(recipe['steps']) + '\n\n' \
    + "The mean rating for this recipe is: " + str(avg_rating) + '\n\n' \
    + "User reviews: " + '\n' \
    + '\n * '.join(reviews['review+rating'].values)

    return recipe_body

def make_food_dataset(data, complementary_data, output_dir="", create_folders=False):
    """
    The folder created should look like this:
    output_dir
    ├── folder 1
    │   ├── recipe 1.txt
    │   ├── recipe 2.txt
    │   ├── ...
    ├── folder 2
    │   ├── recipe 1.txt
    │   ├── recipe 2.txt
    │   ├── ...
    ├── ...

    :param data: pd.DataFrame, the main data to be used
    :param complementary_data: pd.DataFrame, the complementary data to be used, it will be appended to the main data
    :param output_dir: str, the output directory
    
    :return: None
    """

    # Create the directory
    if create_folders:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        else:
            print('Output directory already exists. skipping...')
            # return

    # converting the tags, steps and ingredients to lists
    data['tags'] = data['tags'].apply(lambda x: x[1:-1].replace("'", "").split(', '))
    data['steps'] = data['steps'].apply(lambda x: x[1:-1].replace("'", "").split(', '))
    data['ingredients'] = data['ingredients'].apply(lambda x: x[1:-1].replace("'", "").split(', '))
    data['title'] = data['name']

    complementary_data['review'] = complementary_data['review'].apply(treat_text)
    complementary_data['review+rating'] = '"' + complementary_data['review'] + '"' + ' - User rating: ' + complementary_data['rating'].astype(str)
    
    for recipe in tqdm.tqdm(data.iterrows(), total=len(data), desc="Formatting recipes"):
        recipe = recipe[1]

        # getting the reviews for this recipe
        reviews = complementary_data[complementary_data['recipe_id'] == recipe['id']]

        # ordering by descending date
        reviews = reviews.sort_values('date', ascending=False)

        # getting the average rating
        avg_rating = reviews['rating'].mean()

        # if the average rating is NaN, we will set it to "No reviews"
        if np.isnan(avg_rating):
            avg_rating = "No reviews"

        if create_folders:
            # chosing the folder path:
            # for now, we will put all the recipes in the folder "recipe"
            folder_path = os.path.join(output_dir, 'recipe')
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

        # creating the recipe body
        recipe_body = recipe_file_body(recipe, reviews)

        if create_folders:
            # creating the recipe file
            recipe_path = os.path.join(folder_path, str(recipe['id']) + '.txt')
            with open(recipe_path, 'w') as f:
                try:
                    # something we get the error UnicodeEncodeError: 'charmap' codec can't encode characters in position 1164-1165: character maps to <undefined>
                    f.write(recipe_body)
                except UnicodeEncodeError as e:
                    # we are not been able to write the file because of some special character, se we will replace it
                    try:
                        recipe_body = recipe_body.encode('ascii', 'ignore').decode('ascii')
                        f.write(recipe_body)
                    except Exception as e:
                        print(f'Error writing file {recipe_path}: {e}')
        
        # adding the recipe body to the dataframe
        data.loc[data['id'] == recipe['id'], 'recipe_body'] = recipe_body

    return data
        


def treat_text(text):
    """
    Function responsible for treating the text, removing special characters, \n, etc.
    """
    # reencoding the text
    text = text.encode('ascii', 'ignore').decode('ascii')
    # removing special characters
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\x0b', ' ')
    text = text.replace('\x0c', ' ')
    text = text.replace('\x1c', ' ')
    text = text.replace('\x1d', ' ')
    text = text.replace('\x1e', ' ')
    text = text.replace('\x1f', ' ')
    # removing characters that may cause problems
    text = text.replace('{', ' ')
    text = text.replace('}', ' ')
    text = text.replace('<', ' ')
    text = text.replace('>', ' ')
    text = text.replace('"', ' ')
    # replacing multiple spaces by one
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    return text