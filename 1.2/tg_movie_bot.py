from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, StandardScaler



def process_data(data, vector):

    merged_data_final_1 = pd.concat([merged_data_final, vectorized_data_df], axis=1)
    merged_data_final_1 = merged_data_final_1.dropna()

    scaler = MinMaxScaler()
    standardizer = StandardScaler()
    tfidf = TfidfVectorizer()

    merged_data_final_1.loc[:, ['release_date', 'vote_count', 'revenue']] = scaler.fit_transform(merged_data_final_1[['release_date', 'vote_count', 'revenue']])
    merged_data_final_1.loc[:, ['popularity', 'runtime', 'vote_average']] = standardizer.fit_transform(merged_data_final_1[['popularity', 'runtime', 'vote_average']])

    merged_data_final_1 = merged_data_final_1.drop(['adult', 'budget', 'popularity', 'revenue'], axis = 1)

    return merged_data_final_1

def check_duplicate_titles_ru(df, title, year=None):
    duplicate_titles = df[df['title_y'].str.lower() == title.lower()]
    if year:
        duplicate_titles = duplicate_titles[duplicate_titles['release_date'].astype(str) == year]
        if not duplicate_titles.empty:
            return duplicate_titles['imdb_id'].iloc[0]
    else:
        if len(duplicate_titles) > 1:
            return list(duplicate_titles['release_date'].unique())
        elif len(duplicate_titles) == 1:
            return duplicate_titles['imdb_id'].iloc[0]
    return None

def check_duplicate_titles_en(df, title, year=None):
    duplicate_titles = df[df['title_x'].str.lower() == title.lower()]

    if year:
        duplicate_titles = duplicate_titles[duplicate_titles['release_date'].astype(str) == year]
        if not duplicate_titles.empty:
            print(f"Найден фильм '{title}' с годом выпуска {year}")
            return duplicate_titles['imdb_id'].iloc[0]
    else:
        if len(duplicate_titles) > 1:
            return list(duplicate_titles['release_date'].unique())
        elif len(duplicate_titles) == 1:
            return duplicate_titles['imdb_id'].iloc[0]

    print(f"Фильм '{title}' с годом выпуска {year} не найден")
    return None

# def check_duplicate_titles_en(df, title, year=None):
#     duplicate_titles = df[df['title_x'].str.lower() == title.lower()]
#     if year:
#         filtered_titles = duplicate_titles[duplicate_titles['release_date'].astype(str) == year]
#         if len(filtered_titles) == 1:
#             return filtered_titles['imdb_id'].iloc[0]
#         else:
#             print(f"Фильм '{title}' с годом выпуска {year} не найден")
#             return None
#     else:
#         if len(duplicate_titles) > 1:
#             return list(duplicate_titles['release_date'].unique())
#         elif len(duplicate_titles) == 1:
#             return duplicate_titles['imdb_id'].iloc[0]

#     return None

import numpy as np

def find_most_similar_movies_en(input_tconst, film_vectors, top_n=5):
    if input_tconst in film_vectors.index:
        input_vector = film_vectors.loc[[input_tconst]].values
        all_vectors = film_vectors.drop(index=input_tconst).values

        similarities = cosine_similarity(input_vector, all_vectors)[0]

        indices = similarities.argsort()[-top_n:][::-1]
        similar_ids = film_vectors.iloc[indices].index

        sorted_similarities = similarities[indices]
        print(f"Коэффициенты сходства: {sorted_similarities}")

        if len(similar_ids) == 0:
            return ['Фильмы, похожие на ваш запрос, не найдены.']
        return similar_ids
    else:
        return ['Фильм не найден.']

def find_similar_movies_interactive(input_title, input_language, merged_data, merged_data_final_1, merged_data_final_11, merged_data_final):
    if input_language == 'en':
        input_tconst = check_duplicate_titles_en(merged_data_final, input_title)
    elif input_language == 'ru':
        input_tconst = check_duplicate_titles_ru(merged_data_final, input_title)

    if input_tconst:
        film_vectors = merged_data_final_11.set_index('imdb_id')
        similar_movies_ids = find_most_similar_movies_en(input_tconst, film_vectors)

        if 'Фильмы, похожие на ваш запрос, не найдены.' in similar_movies_ids or 'Фильм не найден.' in similar_movies_ids:
            return similar_movies_ids[0]
            print('не найден или не указан его год222')
        else:
            if input_language == 'en':
                similar_movies_info = merged_data[merged_data['imdb_id'].isin(similar_movies_ids)][['title_x', 'overview']]
                # similar_movies_list = [f"{row['title_x']}: {row['overview']}" for index, row in similar_movies_info.iterrows()]
                # return f"Фильмы, наиболее похожие на '{input_title}':\n\n" + '\n'.join(similar_movies_list)
                similar_movies_list = [f"{row['title_x']}:\n{row['overview']}\n" for index, row in similar_movies_info.iterrows()]
                return "\n".join(similar_movies_list).strip()
                print('Фильмы, наиболее похожие на')
            elif input_language == 'ru':
                similar_movies = merged_data[merged_data['imdb_id'].isin(similar_movies_ids)]['title']
                return f"Фильмы, наиболее похожие на '{input_title}':\n\n" + '\n'.join(similar_movies.tolist())
    else:
        return f"Фильм '{input_title}' не найден или не указан его год."
        print('не найден или не указан его год')

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("RU", callback_data='ru'), InlineKeyboardButton("EN", callback_data='en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите язык/Select language:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['language'] = query.data
    query.edit_message_text(text=f"{query.data}. Теперь введите название фильма/Now enter the name of the movie")

def handle_year_response(update: Update, context: CallbackContext):
    user_data = context.user_data
    year_input = update.message.text
    print(f"handle_year_response: Received year input: {year_input}")  

    if 'awaiting_year' in user_data:
        title = user_data['title']
        language = user_data.get('language', 'en')
        print(f"handle_year_response: Searching for '{title}' in year {year_input}")  
        if language == 'en':
            input_tconst = check_duplicate_titles_en(merged_data_final, title, year_input)
        else:
            input_tconst = check_duplicate_titles_ru(merged_data_final, title, year_input)

        if input_tconst:
            response = find_similar_movies_interactive(title, language, merged_data, merged_data_final_1, merged_data_final_11, merged_data_final)
            update.message.reply_text(response)
        else:
            update.message.reply_text(f"Фильм '{title}' с годом выпуска {year_input} не найден.")
        user_data.clear()
    else:
        print("handle_year_response: Not awaiting year input")  
        update.message.reply_text("Пожалуйста, введите название фильма.")

def handle_message(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = update.message.text
    language = user_data.get('language')

    if not language:
        update.message.reply_text("Пожалуйста, выберите язык, используя кнопки.")
        return

    if 'awaiting_year' in user_data:
        year = text
        title = user_data.get('title')
        if title: 
            if language == 'en':
                input_tconst = check_duplicate_titles_en(merged_data_final, title, year)
            else:
                input_tconst = check_duplicate_titles_ru(merged_data_final, title, year)

            if input_tconst:
                response = find_similar_movies_interactive(text, language, merged_data, merged_data_final_1, merged_data_final_11, merged_data_final)
                update.message.reply_text(response)
            else:
                update.message.reply_text(f"Фильм '{title}' с годом выпуска {year} не найден.")
        else:
            update.message.reply_text("Ошибка: Название фильма не было задано.")
        user_data.clear()
        return

    result = check_duplicate_titles_ru(merged_data_final, text) if language == 'ru' else check_duplicate_titles_en(merged_data_final, text)
    print(result)

    if isinstance(result, list) and len(result) > 1:
        user_data['awaiting_year'] = True
        user_data['title'] = text
        year_list = ', '.join(map(str, result))
        update.message.reply_text(f"Найдено несколько фильмов с названием '{text}'. Укажите год выпуска: {year_list}")
    elif result:
        response = find_similar_movies_interactive(text, language, merged_data, merged_data_final_1, merged_data_final_11, merged_data_final)
        update.message.reply_text(response)
    else:
        update.message.reply_text(f"Фильм '{text}' не найден.")

def main():
    updater = Updater("6934835205:AAFAOGoqNXtGh0acGtZSEXn-RpQkZoME4GA", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^\d{4}$'), handle_year_response))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()