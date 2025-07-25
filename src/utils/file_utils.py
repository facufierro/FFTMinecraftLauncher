def download_file(url, dest, show_progress=True, max_retries=3):
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, stream=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1024 * 32):
            f.write(chunk)
