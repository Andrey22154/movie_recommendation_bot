from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# Загрузка датасета
merged_data = pd.read_parquet('path')

def check_duplicate_titles(df, title, year=None):
    duplicate_titles = df[df['title'].str.lower() == title.lower()]
    if year is not None:
        result = df[(df['title'].str.lower() == title.lower()) & (df['startYear'] == year)]
        if not result.empty:
            return result['tconst'].iloc[0]
        return None
    else:
        if len(duplicate_titles) > 1:
            return list(duplicate_titles['startYear'].unique())
        elif len(duplicate_titles) == 1:
            return [duplicate_titles['startYear'].iloc[0]]
        else:
            return []


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
        if len(similar_ids) == 0:
            return ['Фильмы, похожие на ваш запрос, не найдены.']
        return similar_ids
    else:
        return ['Фильм не найден.']

def search_similar_movies_by_tconst(input_tconst):
    processed_data = process_data(merged_data)
    film_vectors = processed_data.set_index('tconst')
    similar_movies_ids = find_most_similar_movies(input_tconst, film_vectors)

    if 'Фильмы, похожие на ваш запрос, не найдены.' in similar_movies_ids or 'Фильм не найден.' in similar_movies_ids:
        return similar_movies_ids[0]
    else:
        similar_movies = merged_data[merged_data['tconst'].isin(similar_movies_ids)]['title']
        return f"Наиболее похожие фильмы:\n\n" + '\n'.join(similar_movies.tolist())


def start(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! Напиши название фильма, и я найду похожие.')


def handle_message(update: Update, context: CallbackContext):
    # Если ожидаем ввод года, ничего не делаем
    if context.user_data.get('waiting_for_year'):
        return

    text = update.message.text
    context.user_data['title'] = text
    years = check_duplicate_titles(merged_data, text)
    if len(years) > 1:
        context.user_data['waiting_for_year'] = True
        update.message.reply_text(f"Найдены фильмы с названием '{text}'. Укажите год выпуска: {', '.join(years)}")
    elif len(years) == 1:
        input_tconst = check_duplicate_titles(merged_data, text, years[0])
        response = search_similar_movies_by_tconst(input_tconst)
        update.message.reply_text(response)
    else:
        update.message.reply_text(f"Фильм '{text}' не найден.")

def handle_year_response(update: Update, context: CallbackContext):

    if context.user_data.get('waiting_for_year'):
        year = update.message.text
        title = context.user_data['title']
        input_tconst = check_duplicate_titles(merged_data, title, year)
        if input_tconst:
            response = search_similar_movies_by_tconst(input_tconst)
            update.message.reply_text(response)
            context.user_data.clear()
        else:
            update.message.reply_text(f"Фильм '{title}' с годом выпуска {year} не найден.")
            context.user_data.clear()
    else:
        update.message.reply_text("Пожалуйста, введите название фильма.")


def main():
    updater = Updater("KEY", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'^\d{4}$'), handle_year_response))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
