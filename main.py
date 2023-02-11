import os
import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError
from urllib.parse import urljoin


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError()


def check_redirect_for_download(response):
    if len(response.history) > 1:
        raise requests.HTTPError()


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    check_redirect_for_download(response)

    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)


def download_images(url, filename, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()

    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)


def main():
    os.makedirs('./books', exist_ok=True)
    os.makedirs('./images', exist_ok=True)
    sep = ' \xa0 :: \xa0 '

    for book_id in range(1, 11):
        url_book = f'https://tululu.org/b{book_id}/'
        try:
            response = requests.get(url_book)
            response.raise_for_status()
            check_for_redirect(response)
        except HTTPError:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        book_title_text = soup.find('h1').text
        book_title = book_title_text.split(sep)[0].strip()
        book_filename = f'{book_id}. {book_title}.txt'

        url_book_content = f'http://tululu.org/txt.php?id={book_id}'
        try:
            download_txt(url_book_content, book_filename)
        except HTTPError:
            continue
    
        book_image_src = soup.find(class_='bookimage').find('img')['src']
        book_image_url = urljoin(url_book, book_image_src)
        image_filename = book_image_src.split('/')[-1]
        download_images(book_image_url, image_filename)


if __name__ == '__main__':
    main()