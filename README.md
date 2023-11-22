# Movie Recommendation Telegram Bot

## Overview
This project implements a Telegram bot for movie recommendations. Users can interact with the bot by sending a movie title, and in response, the bot suggests similar movies based on the input. The bot handles cases where there are multiple movies with the same name by asking for the year of release to accurately identify the movie.

## Features
- Movie similarity search: Users can enter a movie title to receive a list of similar movies.
- Duplicate title handling: If there are multiple movies with the same title, the bot prompts the user to specify the year of release.
- Data processing: The bot uses a pre-processed dataset to find similar movies based on user input.

## How It Works
1. The user sends a movie title to the Telegram bot.
2. If the bot identifies multiple movies with the same title, it asks the user to specify the year of release.
3. Once the exact movie is identified, the bot processes the dataset to find and return a list of similar movies.

## Data Processing
The dataset is pre-processed using various techniques such as normalization, standardization, and TF-IDF vectorization to convert movie features into numerical vectors. These vectors are then used to calculate similarity scores.

## Similarity Calculation
The bot uses cosine similarity to determine how closely related each movie in the dataset is to the user's input. It then suggests movies with the highest similarity scores.

## Technologies Used
- Python
- Pandas for data manipulation
- Scikit-learn for data preprocessing and similarity calculation
- Telegram Bot API for interacting with users

## Setup and Usage
To use this bot:
1. Clone the repository to your local machine.
2. Install the required Python packages.
3. Run the bot script and interact with it through Telegram.

## License
This project is licensed under the terms of the MIT license.

