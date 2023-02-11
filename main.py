import os
import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from requests import HTTPError


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError()


def check_redirect_for_download(response):
    if len(response.history) > 1:
        raise requests.HTTPError()


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()

    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)


def main():
    os.makedirs('./books', exist_ok=True)
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
        filename = f'{book_id}. {book_title}.txt'

        url_book_content = f'http://tululu.org/txt.php?id={book_id}'
        try:
            response = requests.get(url_book_content)
            response.raise_for_status()
            check_redirect_for_download(response)
        except HTTPError:
            continue
    
        download_txt(url_book_content, filename=filename)

if __name__ == '__main__':
    main()