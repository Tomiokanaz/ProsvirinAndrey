import sqlite3
import requests

# Подключаемся к базе данных (если файла с базой нет, он будет создан)
conn = sqlite3.connect('posts.db')
cursor = conn.cursor()

# Создаем таблицу posts
cursor.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    body TEXT
)
''')

# Сохраняем изменения
conn.commit()

# Выполняем GET-запрос к API и загружаем данные
response = requests.get('https://jsonplaceholder.typicode.com/posts')
posts_data = response.json()

# Подготовка данных для вставки
posts_to_insert = [(post['id'], post['userId'], post['title'], post['body']) for post in posts_data]

# Вставляем данные в таблицу posts
cursor.executemany('''
INSERT OR IGNORE INTO posts (id, user_id, title, body)
VALUES (?, ?, ?, ?)
''', posts_to_insert)

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()
