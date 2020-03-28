#!/usr/bin/python3

import pickle
import re
import unicodedata

import feedparser
import requests

consumer_key = ""  # app key
access_token = ""  # my key


def slugify(s):
    slug = s.replace("'s", "")
    slug = unicodedata.normalize("NFKD", slug)
    slug = slug.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"[-]+", "-", slug)

    return slug


def login():
    request_token = requests.post(
        "https://getpocket.com/v3/oauth/request",
        json={
            "consumer_key": consumer_key,
            "redirect_uri": "https://finch.am/rss-integration/done/",
        },
        headers={"X-Accept": "application/json"},
    ).json()["code"]
    print(
        "Please go to https://getpocket.com/auth/authorize?request_token=%s&redirect_uri=https://finch.am/rss-integration/done/"
        % request_token
    )
    input("Press Enter once done...")
    access_token = requests.post(
        "https://getpocket.com/v3/oauth/authorize",
        json={"consumer_key": consumer_key, "code": request_token},
        headers={"X-Accept": "application/json"},
    ).json()["access_token"]
    return access_token


def api(method, data, version="v3"):
    data["consumer_key"] = consumer_key
    data["access_token"] = access_token

    try:
        response = requests.post(
            "https://getpocket.com/%s/%s" % (version, method),
            json=data,
            headers={"X-Accept": "application/json"},
        )
        json = response.json()
    except:
        print(response.text)
        raise

    return json


def load():
    with open("state", "rb") as f:
        return pickle.load(f)


def save(state):
    with open("state", "wb") as f:
        pickle.dump(state, f)


if __name__ == "__main__":
    try:
        state = load()
    except:
        state = {"seen": set()}

    if "access_token" not in state:
        state["access_token"] = login()
        save(state)

    if "seen" not in state:
        state["seen"] = set()
        save(state)

    access_token = state["access_token"]

    feeds = ["http://www.righto.com/feeds/posts/default?alt=rss"]

    for url in feeds:
        d = feedparser.parse(url)
        feed_title = d["feed"].get("title", "rss")
        for entry in d.entries:
            url = entry.link
            title = entry.title
            tags = ", ".join(list(set([slugify(feed_title), "rss"])))
            if url not in state["seen"]:
                state["seen"].add(url)
                print("New post: %s from %s" % (title, feed_title))
                result = api("add", {"url": url, "title": title, "tags": tags})
        save(state)
