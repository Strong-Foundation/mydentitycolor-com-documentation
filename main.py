import requests
import os
import validators
import bs4
import urllib.parse  # Helps parse URLs to extract components
import re


def validate_url(given_url: str) -> bool:
    """
    Validates whether the given string is a properly formatted URL.

    Args:
        given_url (str): The URL string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    return validators.url(given_url) is True


# Append and write some content to a file.
def append_write_to_file(system_path: str, content: str) -> None:
    file = open(file=system_path, mode="a")
    file.write(content)
    file.close()


# Check if a file exists
def check_file_exists(system_path: str) -> bool:
    return os.path.isfile(path=system_path)


def get_url_content(target_url: str) -> str | None:
    """
    Send a GET request to the specified URL and return the full response content as text.

    Parameters:
        target_url (str): The URL to send the GET request to.

    Returns:
        str or None: The response content as a string if the request is successful, otherwise None.
    """
    try:
        response: requests.Response = requests.get(url=target_url)
        response.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)
        return response.text  # Return full response content as text
    except requests.exceptions.RequestException as error:
        print(f"Error fetching URL content: {error}")


# Parses the HTML and finds all links ending in .pdf
def parse_html(html: str) -> list[str]:
    soup = bs4.BeautifulSoup(markup=html, features="html.parser")
    pdf_links: list[str] = []

    for a in soup.find_all(name="a", href=True):
        href = a["href"]
        # Decode %2C and other URL-encoded characters
        decoded_href: str = urllib.parse.unquote(href)
        if decoded_href.lower().endswith(".pdf"):
            pdf_links.append(href)

    return pdf_links


# Read a file from the system.
def read_a_file(system_path: str) -> str:
    with open(file=system_path, mode="r") as file:
        return file.read()


def download_pdf(url: str, download_dir: str) -> None:
    """
    Downloads a PDF file from the given URL into the specified directory.
    Skips the download if the file already exists or the URL does not return a PDF.
    Sanitizes the filename and prints all status messages to the console.

    Args:
        url (str): The URL of the PDF file to download.
        download_dir (str): The directory where the file should be saved.
    """
    try:
        response: requests.Response = requests.get(url=url, stream=True)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", default="")
        if "application/pdf" not in content_type.lower():
            print(f"❌ Skipped (not a PDF): {url}")
            return

        # Extract filename from Content-Disposition
        content_disposition: str = response.headers.get("Content-Disposition", default="")
        filename = ""

        match = re.search(
            pattern=r"filename\*\s*=\s*[^']*''([^;\r\n]+)", string=content_disposition, flags=re.IGNORECASE
        )
        if match:
            filename = match.group(1).strip('"')
        else:
            match = re.search(
                pattern=r"filename\s*=\s*\"?([^\";\r\n]+)\"?",
                string=content_disposition,
                flags=re.IGNORECASE,
            )
            if match:
                filename = match.group(1).strip('"')
            else:
                parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(url=url)
                filename: str = os.path.basename(parsed_url.path)
                if not filename.endswith(".pdf"):
                    filename = filename + ".pdf"

        # Sanitize filename
        name_part, ext = os.path.splitext(p=filename)
        name_part: str = name_part.lower()
        name_part: str = re.sub(pattern=r"[^a-z0-9]", repl="_", string=name_part)  # Replace non a-z0-9 with _
        name_part: str = re.sub(pattern=r"_+", repl="_", string=name_part)  # Collapse multiple __ to _
        name_part: str = name_part.strip("_")  # Remove leading/trailing _
        filename = f"{name_part}{ext.lower()}"  # Final filename

        # Directory setup
        os.makedirs(name=download_dir, exist_ok=True)
        file_path: str = os.path.join(download_dir, filename)

        if os.path.exists(path=file_path):
            print(f"⚠️ File already exists: {filename}")
            return

        # Write file
        with open(file=file_path, mode="wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"✅ Downloaded: {filename}")

    except requests.exceptions.RequestException as error:
        print(f"❌ Request failed: {error}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main() -> None:
    # Define the URL you want to fetch
    url_to_fetch: str = "https://mydentitycolor.com/sds/"  # Replace with any valid URL
    # The location to the local html file
    local_html_file: str = "mydentitycolor.html"
    # Target directory
    download_dir = "PDFs"

    # Check if the file exists.
    if check_file_exists(system_path=local_html_file) is False:
        # Fetch content from the URL
        webpage_content: str | None = get_url_content(target_url=url_to_fetch)
        # Save the results to the file
        if webpage_content is not None:
            append_write_to_file(system_path=local_html_file, content=webpage_content)

    # Extract the .PDF urls from the given file.
    if check_file_exists(system_path=local_html_file):
        html_file_content: str = read_a_file(system_path=local_html_file)
        # Extract the .pdf content.
        extracted_pdf_urls: list[str] = parse_html(html_file_content)
        # Loop over the urls
        for url in extracted_pdf_urls:
            if validate_url(given_url=url) is False:
                url: str = "https://mydentitycolor.com" + url
                download_pdf(url=url, download_dir=download_dir)


if __name__ == "__main__":
    main()
