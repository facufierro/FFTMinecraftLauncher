import requests
import zipfile
from tqdm import tqdm


def download_file(url, dest, show_progress=True, max_retries=3):
    """Download a file with progress bar and validate as zip if .jar/.zip. Retries on failure."""
    for attempt in range(1, max_retries + 1):
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, stream=True)
        total = int(r.headers.get("content-length", 0))
        print(
            f"[DEBUG] Downloading {url} (attempt {attempt}/{max_retries}), HTTP status: {r.status_code}"
        )
        if show_progress:
            bar = tqdm(
                desc=dest.name, total=total, unit="B", unit_scale=True, leave=False
            )
        else:
            bar = None
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1024 * 32):
                f.write(chunk)
                if bar:
                    bar.update(len(chunk))
        if bar:
            bar.close()
        # Print file size after download
        try:
            size = dest.stat().st_size
            print(f"[DEBUG] Downloaded file size: {size} bytes")
        except Exception:
            print(f"[DEBUG] Could not stat file {dest}")
        # Validate as zip if .jar or .zip
        is_zip = str(dest).endswith(".jar") or str(dest).endswith(".zip")
        valid = True
        if is_zip:
            try:
                with zipfile.ZipFile(dest, "r") as zf:
                    bad = zf.testzip()
                    if bad is not None:
                        print(f"[WARN] Corrupt zip entry {bad} in {dest}, retrying...")
                        valid = False
            except Exception as e:
                print(
                    f"[WARN] Downloaded file {dest} is not a valid zip: {e}, retrying..."
                )
                # Print first 200 bytes of file for debugging
                try:
                    with open(dest, "rb") as f:
                        snippet = f.read(200)
                        print(f"[DEBUG] First 200 bytes of file: {snippet}")
                except Exception:
                    print(f"[DEBUG] Could not read file {dest}")
                valid = False
        if valid:
            return
        else:
            try:
                dest.unlink()
            except Exception:
                pass
            if attempt == max_retries:
                # Print first 200 bytes of HTTP response if not valid
                try:
                    r2 = requests.get(url)
                    print(f"[DEBUG] HTTP status: {r2.status_code}")
                    print(
                        f"[DEBUG] First 200 bytes of HTTP response: {r2.content[:200]}"
                    )
                except Exception:
                    print(f"[DEBUG] Could not fetch HTTP response for {url}")
                raise Exception(
                    f"Failed to download a valid file from {url} after {max_retries} attempts."
                )
