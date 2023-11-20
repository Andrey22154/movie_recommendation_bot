from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, StandardScaler



# Загрузка датасета
merged_data = pd.read_parquet('C:\\Users\\Администратор\\Downloads\\merged_data.parquet')

# Функция для проверки дубликатов названий фильмов
def check_duplicate_titles(df, title):
    duplicate_titles = df[df['title'].str.lower() == title.lower()]
    if len(duplicate_titles) > 1:
        print('Есть фильмы схожего названия с годами выпуска: ', duplicate_titles['startYear'].unique(),
              'введите ваш год выпуска')
        film_year = input('')
        result = df[(df['title'].str.lower() == title.lower()) & (df['startYear'] == film_year)]
        if not result.empty:
            return result['tconst'].iloc[0]
        else:
            return None
    elif len(duplicate_titles) == 1:
        result = df[(df['title'].str.lower() == title.lower()) & (df['startYear'] == duplicate_titles['startYear'].iloc[0])]
        if not result.empty:
            return result['tconst'].iloc[0]
        else:
            return None
    else:
        return 'Фильм не найден'

def process_data(df):

    df = df.copy()
    df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce')
    df = df[df['startYear'] >= 1990]
    scaler = MinMaxScaler()
    standardizer = StandardScaler()
    tfidf = TfidfVectorizer()

    df.loc[:, ['startYear', 'numVotes']] = scaler.fit_transform(df[['startYear', 'numVotes']])
    df.loc[:, 'averageRating'] = standardizer.fit_transform(df[['averageRating']])
    tfidf_genres = tfidf.fit_transform(df['genres'])
    tfidf_genres_df = pd.DataFrame(tfidf_genres.toarray(), columns=tfidf.get_feature_names_out())

    return pd.concat([df.drop(columns=['genres', 'region', 'title']), tfidf_genres_df], axis=1).dropna()

def find_most_similar_movies(input_tconst, film_vectors, top_n=5):
    if input_tconst in film_vectors.index:
        input_vector = film_vectors.loc[[input_tconst]].values
        all_vectors = film_vectors.drop(index=input_tconst).values
        similarities = cosine_similarity(input_vector, all_vectors)[0]
        indices = similarities.argsort()[-top_n:][::-1]
        similar_ids = film_vectors.iloc[indices].index

        if len(similar_ids) == 0:  # Проверяем, есть ли результаты
            return ['Фильмы, похожие на ваш запрос, не найдены.']
        return similar_ids
    else:
        return ['Фильм не найден.']
def start(update, context):
    update.message.reply_text('Привет! Напиши название фильма, и я найду похожие.')


def handle_message(update, context):
    text = update.message.text
    response = search_similar_movies(text)
    update.message.reply_text(response)


def search_similar_movies(input_title):
    input_tconst = check_duplicate_titles(merged_data, input_title)
    if input_tconst:
        processed_data = process_data(merged_data)
        film_vectors = processed_data.set_index('tconst')
        similar_movies_ids = find_most_similar_movies(input_tconst, film_vectors)

        if 'Фильмы, похожие на ваш запрос, не найдены.' in similar_movies_ids or 'Фильм не найден.' in similar_movies_ids:
            return similar_movies_ids[0]
        else:
            similar_movies = merged_data[merged_data['tconst'].isin(similar_movies_ids)]['title']
            return f"Фильмы, наиболее похожие на '{input_title}':\n" + '\n'.join(similar_movies.tolist())
    else:
        return f"Фильм '{input_title}' не найден или не указан его год."


def main():
    updater = Updater("6934835205:AAFAOGoqNXtGh0acGtZSEXn-RpQkZoME4GA", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
