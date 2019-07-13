import re
from html.parser import HTMLParser
from typing import List, Tuple

import requests


class PostSnippetParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.post_urls = []

    def handle_starttag(self, tag, attrs):
        snippet = False
        href = None

        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    href = value
                if name == "class" and "td-image-wrap" in value:
                    snippet = True

        if snippet and href:
            self.post_urls.append(href)


def fetch_posts(pages=10) -> List[Tuple[int, str, str]]:
    result = []
    for page_number in range(1, 0, -1):
        result += posts_from_page(page_number=page_number)
    return result


def posts_from_page(page_number=1) -> Tuple[int, str, str]:
    response = requests.post(
        "https://rap.de/wp-admin/admin-ajax.php?v=9.5",
        data={
            "action": "td_ajax_loop",
            "loopState[moduleId]": 4,
            "loopState[currentPage]": page_number,
            "loopState[atts][category_id]": 23,
        },
    )
    html = response.json()["server_reply_html_data"]

    parser = PostSnippetParser()
    parser.feed(html)

    posts = [post_from_url(post_url) for post_url in parser.post_urls]

    return posts


def post_from_url(url: str) -> Tuple[int, str, str]:
    match = re.search(r"^https://rap.de/soundandvideo/([0-9]+)-(.*)/$", url)
    return match.group(1, 2) + (url,)


def extract_video_ids(posts: List[Tuple[int, str, str]]) -> List[str]:
    video_ids = []
    for post in posts:
        response = requests.get(post[2])
        parser = PostParser()
        parser.feed(response.text)
        video_ids += parser.video_ids
    return video_ids


class PostParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.video_ids: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "iframe":
            for name, value in attrs:
                if name == "src":
                    match = re.search(
                        r"https://www\.youtube\.com/embed/(.*)\?feature=oembed", value
                    )
                    if match:
                        self.video_ids.append(match.group(1))
