import argparse
import os
import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError
from urllib.parse import urljoin, urlsplit


def check_for_redirect(response):
    if response.url == 'https://tululu.org/':
        raise requests.HTTPError()


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)


def download_images(image_url, filename, folder='images/'):
    response = requests.get(image_url)
    response.raise_for_status()

    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)
     

def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    sep = ' \xa0 :: \xa0 '
    title_and_author = title_tag.text.split(sep)

    title = title_and_author[0].strip()
    author = title_and_author[1].strip()

    genres = soup.find('span', class_='d_book').findAll('a')
    genres_text = [genre.text for genre in genres]

    image_src = soup.find(class_='bookimage').find('img')['src']
    image_url = urljoin(response.url, image_src)

    book_comments = soup.findAll(class_='texts')
    book_comments_texts = [
        comment.find(class_='black').text for comment in book_comments
    ]

    book_content = {
        'title': title,
        'author': author,
        'genres': genres_text,
        'image_url': image_url,
        'comments': book_comments_texts,
    }
    return book_content


def main():
    parser = argparse.ArgumentParser(
        description='Скачивание книг по начальному и конечному id'
    )
    parser.add_argument('start_id', nargs='?', default=1, type=int)
    parser.add_argument('end_id', nargs='?', default=10, type=int)
    args = parser.parse_args()

    os.makedirs('./books', exist_ok=True)
    os.makedirs('./images', exist_ok=True)

    for book_id in range(args.start_id, args.end_id + 1):
        url_book = f'https://tululu.org/b{book_id}/'
        try:
            response = requests.get(url_book)
            response.raise_for_status()
            check_for_redirect(response)
        except HTTPError:
            continue
        
        book_content = parse_book_page(response)

        book_image_url = book_content['image_url']
        book_image_name = urlsplit(book_image_url).path.split('/')[-1]
        download_images(book_content['image_url'], book_image_name)

        url_book_download = f'http://tululu.org/txt.php?id={book_id}'
        book_filename = f'{book_id}. {book_content["title"]}.txt'
        try:
            download_txt(url_book_download, book_filename)
        except HTTPError:
            continue

if __name__ == '__main__':
    main()
