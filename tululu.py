import argparse
import os
import requests
import time

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError, ConnectionError
from urllib.parse import urljoin, urlsplit


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.HTTPError()


def download_txt(url, payload, filename, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)

    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'wb') as file:
        file.write(response.text)


def download_image(image_url, image_filename, folder='images/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(image_url)
    response.raise_for_status()

    image_filename = sanitize_filename(image_filename)
    full_path = os.path.join(folder, image_filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)


def download_comments(comments, filename, folder='comments/'):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename)
    with open(full_path, 'w') as file:
        [file.write(f'{text}\n') for text in comments]


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    title, author = title_tag.text.split(' \xa0 :: \xa0 ')
    title, author = title.strip(), author.strip()
    genres = soup.find('span', class_='d_book').findAll('a')
    genres_text = [genre.text for genre in genres]
    image_src = soup.find(class_='bookimage').find('img')['src']
    image_url = urljoin(response.url, image_src)
    book_comments = soup.findAll(class_='texts')
    book_comments_text = [
        comment.find(class_='black').text for comment in book_comments
    ]
    book_content = {
        'title': title,
        'author': author,
        'genres': genres_text,
        'image_url': image_url,
        'comments': book_comments_text,
    }
    return book_content


def main():
    parser = argparse.ArgumentParser(
        description='Скачивание книг по начальному и конечному id'
    )
    parser.add_argument(
        'start_id',
        nargs='?',
        default=1,
        type=int,
        help='start_id (default: 1)',
    )
    parser.add_argument(
        'end_id',
        nargs='?',
        default=10,
        type=int,
        help='end_id (default: 10)',
    )
    args = parser.parse_args()

    os.makedirs('./books', exist_ok=True)  

    for book_id in range(args.start_id, args.end_id + 1):
        payload = {'id': book_id}
        book_url = f'https://tululu.org/b{book_id}/'
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            check_for_redirect(response)
        except HTTPError as error:
            print(f'HTTPError: book id={book_id} not found')
            continue
        except ConnectionError as error:
            print(f"ConnectionError: can't connect to \
                  the book id={book_id} page")
            time.sleep(5)
            continue

        book_content = parse_book_page(response)
        book_filename = f'{book_id}. {book_content["title"]}.txt'

        if book_content['comments']:
            download_comments(book_content['comments'], book_filename)
        
        book_image_url = book_content['image_url']
        book_image_name = urlsplit(book_image_url).path.split('/')[-1]
        try:
            download_image(book_image_url, book_image_name)
        except HTTPError:
            print(f"HTTPError: book id={book_id} image can't \
                  be downloaded")
            continue
        except ConnectionError as error:
            print(f"ConnectionError: can't connect to \
                  the book id={book_id} image url")
            time.sleep(5)
            continue

        book_download_url = 'http://tululu.org/txt.php'
        try:
            download_txt(book_download_url, payload, book_filename)
        except HTTPError:
            print(f"HTTPError: book id={book_id} can't be downloaded")
            continue
        except ConnectionError as error:
            print(f"ConnectionError: can't connect to \
                  download the book id={book_id}")
            time.sleep(5)
            continue

if __name__ == '__main__':
    main()
