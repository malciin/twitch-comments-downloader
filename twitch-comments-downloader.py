# ClientId [a.Q.Www]={clientID:"
# https://api.twitch.tv/v5/videos/998053793/comments?content_offset_seconds=0
# https://api.twitch.tv/v5/videos/998053793/comments?cursor=eyJpZCI6Ijc4NjkyZjQ3LWVjMjQtNDJkOC1hODQ3LWFlZWQ5YmRlMjM1YiIsImhrIjoiYnJvYWRjYXN0OjQxNTQ3NTAwNTU3Iiwic2siOiJBQUFEZ1RHY2JvQVdlSThfeHFOZGdBIn0f


import urllib.request
import os.path
import os
import json
from types import SimpleNamespace
import hashlib
import re

def download(url, clientId = None, cache = True):
    hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    directory = '_cache' + os.path.sep + hash[0] + os.path.sep + hash[1]
    os.makedirs(directory, exist_ok=True)
    htmlFile = directory + os.path.sep + hash

    if cache and os.path.isfile(htmlFile):
         with open(htmlFile, 'r', encoding='utf-8') as file:
            data = file.read()
            return data

    request = urllib.request.Request(url)
    if clientId != None:
        request.add_header('Client-Id', clientId)

    try:
        resource = urllib.request.urlopen(request)
    except urllib.error.HTTPError as httpError:
        error = httpError.read().decode('utf-8')
        print(error)
        return None

    data = resource.read().decode('utf-8')

    if cache:
        with open(htmlFile, 'w', encoding='utf-8') as file:
            file.write(data)
    return data

def get_HH_mm_ss_fromSeconds(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%02d:%02d:%02d"%(hours,minutes,seconds)

if __name__ == "__main__":
    link = os.sys.argv[1]
    videoId = link.split('/')[-1]
    core = download(link)

    javascriptUrls = [url for url in re.findall('https?:\/\/[\w/\-?=%.]+\.[\w/\-&?=%.]+', core) if url.endswith('.js')]

    clientCodeUrl = next(javascriptUrl for javascriptUrl in javascriptUrls if 'assets/core-' in javascriptUrl)
    clientCode = download(clientCodeUrl)
    clientId = re.findall('\[a.Q.Www\]={clientID:"([a-zA-Z0-9]+)"', clientCode)[0]

    print(f'Using ClientId: "{clientId}"')

    comments = []
    result = download(f'https://api.twitch.tv/v5/videos/{videoId}/comments?content_offset_seconds=0', clientId = clientId)
    while True:
        responseObject = json.loads(result)
        comments.extend(responseObject['comments'])
        print(f'Downloaded so far {len(comments)} comments. Processed {get_HH_mm_ss_fromSeconds(float(responseObject["comments"][-1]["content_offset_seconds"]))} of a video.')
        if '_next' not in responseObject:
            break
        result = download(f'https://api.twitch.tv/v5/videos/{videoId}/comments?cursor={responseObject["_next"]}', clientId = clientId)
    print(f'All comments downloaded. Creating {videoId}.json file')
    with open(f'{videoId}.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(comments, indent=4))
