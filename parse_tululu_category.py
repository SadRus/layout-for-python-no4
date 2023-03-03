import argparse
import json
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


def download_txt(url, payload, filename, dest_folder = './'):
    folder = os.path.join(dest_folder, 'books/')
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    filename = sanitize_filename(filename)
    full_path = os.path.join(folder, filename) 
    with open(full_path, 'w') as file:
        file.write(response.text)


def download_image(image_url, image_filename, dest_folder = './'):
    folder = os.path.join(dest_folder, 'images/')
    os.makedirs(folder, exist_ok=True)
    response = requests.get(image_url)
    response.raise_for_status()

    image_filename = sanitize_filename(image_filename)
    full_path = os.path.join(folder, image_filename) 
    with open(full_path, 'wb') as file:
        file.write(response.content)


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.select_one('h1')
    title, author = title_tag.text.split(' \xa0 :: \xa0 ')
    title, author = title.strip(), author.strip()
    img_src = soup.select_one('.bookimage img')['src']
    book_path = urljoin('books/', f'{title}.txt')
    book_comments = soup.select('.texts .black')
    book_comments_text = [comment.text for comment in book_comments]
    genres = soup.select('.ow_px_td span.d_book a')
    genres_text = [genre.text for genre in genres]
    book_content = {
        'title': title,
        'author': author,
        'img_src': img_src,
        'book_path': book_path,
        'comments': book_comments_text,
        'genres': genres_text,
    }
    return book_content


def get_pages_count(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    pages = soup.select('.ow_px_td .center .npage')
    return int(pages[-1].text)


def create_parser(pages_count):
    parser = argparse.ArgumentParser(
        description='Скачивание книг по начальной и конечной странице'
    )
    parser.add_argument(
        '--start_page',
        default=1,
        type=int,
        metavar='',
        help='start page (default: 1)',
    )
    parser.add_argument(
        '--end_page',
        default=pages_count,
        type=int,
        metavar='',
        help='end page (default: last page num)',
    )
    parser.add_argument(
        '-d',
        '--dest_folder',
        default='./',
        type=str,
        metavar='',
        help='path to results of parsing (default: "./")',
    )
    parser.add_argument(
        '-i',
        '--skip_imgs',
        action='store_true',
        default=False,
        help='skip download book images. True or False (default: False)',
    )
    parser.add_argument(
        '-t',
        '--skip_txt',
        action='store_true',
        default=False,
        help='skip download book txt. True or False (default: False)',
    )
    parser.add_argument(
        '-j',
        '--json_path',
        default='./',
        type=str,
        metavar='',
        help='path for json result of parsing (default: "./")',
    )
    return parser


def main():
    url = 'https://tululu.org/l55/'
    pages_count = get_pages_count(url)

    parser = create_parser(pages_count)
    args = parser.parse_args()

    books_content = []
    for page in range(args.start_page, args.end_page):
        url = f'https://tululu.org/l55/{page}/'
        response = requests.get(url)
        response.raise_for_status()
        check_for_redirect(response)
        soup = BeautifulSoup(response.text, 'lxml')

        books = soup.select('.ow_px_td table')
        for book in books:
            book_id = book.select_one('a')['href'][2:-1]
            payload = {'id': book_id}
            book_url = f'https://tululu.org/b{book_id}/'
            try:
                response = requests.get(book_url)
                response.raise_for_status()
                check_for_redirect(response)
            except HTTPError:
                print(f"HTTPError: book id={book_id} can't be downloaded")
                continue
            except ConnectionError as error:
                print(f"ConnectionError: can't connect to download",
                       "the book id={book_id}")
                time.sleep(5)
                continue

            book_content = parse_book_page(response)
            book_filename = f'{book_id}. {book_content["title"]}.txt'
            books_content.append(book_content)

            book_img_src = book_content['img_src']
            book_image_url = urljoin(response.url, book_img_src)
            book_image_name = urlsplit(book_image_url).path.split('/')[-1]
            if not args.skip_imgs:
                try:
                    download_image(
                        book_image_url,
                        book_image_name,
                        dest_folder=args.dest_folder
                    )
                except HTTPError:
                    print(f"HTTPError: book id={book_id} image can't be downloaded")
                    continue
                except ConnectionError as error:
                    print(f"ConnectionError: can't connect to download",
                           "the book id={book_id}")
                    time.sleep(5)
                    continue

            book_download_txt_url = 'http://tululu.org/txt.php'
            if not args.skip_txt:
                try:
                    download_txt(book_download_txt_url,
                                 payload,
                                 book_filename,
                                 dest_folder=args.dest_folder
                    )
                except HTTPError:
                    print(f"HTTPError: book id={book_id} text can't be downloaded")
                    continue
                except ConnectionError as error:
                    print(f"ConnectionError: can't connect to download",
                           "the book id={book_id}")
                    time.sleep(5)
                    continue
    os.makedirs(args.json_path, exist_ok=True)
    json_fullpath = os.path.join(args.json_path, 'books_content.json')
    with open(json_fullpath, 'w') as file:
        json.dump(books_content, file, ensure_ascii=False)

if __name__ == '__main__':
    main()
