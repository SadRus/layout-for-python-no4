import os
import requests

from pathlib import Path


path = './files'
Path(path).mkdir(exist_ok=True)

for i in range(1, 11):
    url = f'https://tululu.org/txt.php?id={i}'
    response = requests.get(url)
    response.raise_for_status()

    filename = f'Id{i}.txt'
    with open(Path(path).joinpath(filename), 'wb') as file:
        file.write(response.content)