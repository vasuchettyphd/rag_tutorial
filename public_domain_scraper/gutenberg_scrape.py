import os
import re
import random
import requests
from bs4 import BeautifulSoup

def get_top_gutenberg_ids():
    """
    Scrape Gutenberg's 'Top 100' page to get a list of eBook IDs.
    Returns a list of numeric IDs as strings.
    """
    url = "https://www.gutenberg.org/browse/scores/top"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}, status code {response.status_code}")

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Find links like /ebooks/12345
    links = soup.select("a[href^='/ebooks/']")
    ebook_ids = set()

    for a in links:
        href = a.get("href", "")
        # Extract numeric ID from /ebooks/<ID>
        match = re.search(r"/ebooks/(\d+)", href)
        if match:
            ebook_id = match.group(1)
            ebook_ids.add(ebook_id)

    return list(ebook_ids)


def download_ebooks_by_id(ebook_ids, output_dir="books"):
    """
    Given a list of Gutenberg ebook IDs, try downloading each as <ID>-0.txt
    into 'output_dir'.
    """
    os.makedirs(output_dir, exist_ok=True)

    for ebook_id in ebook_ids:
        txt_url = f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-0.txt"
        print(f"Downloading {txt_url} ...")

        resp = requests.get(txt_url)
        if resp.status_code == 200:
            filename = os.path.join(output_dir, f"{ebook_id}.txt")
            with open(filename, "wb") as f:
                f.write(resp.content)
            print(f"Saved {filename}")
        else:
            print(f"Failed to download eBook #{ebook_id} from {txt_url}. Status: {resp.status_code}")


def main():
    print("Scraping top Gutenberg IDs...")
    all_ids = get_top_gutenberg_ids()
    print(f"Found {len(all_ids)} ebook IDs on Top 100 page.")

    # Pick 20 random IDs (or however many you want)
    num_to_download = 20
    chosen_ids = random.sample(all_ids, min(num_to_download, len(all_ids)))
    print(f"Randomly chosen eBook IDs: {chosen_ids}")

    print("Downloading eBooks to 'books/'...")
    download_ebooks_by_id(chosen_ids, output_dir="books")

if __name__ == "__main__":
    main()