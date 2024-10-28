import re
import time
from urllib.parse import urlparse, urljoin
import utils
from bs4 import BeautifulSoup

# dict to store last time domain was accessed 
domain_access_times = {}
# dict to store visit counts for URLs
visited_urls = {}

def scraper(url, resp):
    # politeness delay 
    enforce_politeness(url)

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link) and not is_trap(link)]  # Added is_trap check

def enforce_politeness(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # enforce delay if domain has been accessed recently 
    if domain in domain_access_times:
        time_since_last_access = time.time() - domain_access_times[domain]
        if time_since_last_access < 0.5:
            time.sleep(0.5 - time_since_last_access)
    
    # update last access time for domain 
    domain_access_times[domain] = time.time()

def extract_next_links(url, resp):
    # check if response is ok + content available 
    if resp.status != 200 or resp.raw_response.content is None:
        return []

    # parse HTML 
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

    # extract + filter links
    scrapped_links = set()
    for link in soup.find_all('a', href=True):
        s_link = urljoin(url, link.get('href'))
        if s_link:
            scrapped_links.add(s_link)

    return list(scrapped_links)

def is_valid(url):
    try:
        parsed = urlparse(url)

        # make sure URL is http or https
        if parsed.scheme not in {"http", "https"}:
            return False

        # allow only specified domains
        allowed_domains = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu", "today.uci.edu"]
        if not any(domain in parsed.netloc for domain in allowed_domains):
            return False

        # allow only today.uci.edu/department/information_computer_sciences/ paths
        if "today.uci.edu" in parsed.netloc and not parsed.path.startswith("/department/information_computer_sciences/"):
            return False

        # avoid links with unwanted extensions
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise

def is_trap(url):
    parsed = urlparse(url)
    base_url = parsed.scheme + "://" + parsed.netloc + parsed.path

    # count visits to base URL
    if base_url in visited_urls:
        visited_urls[base_url] += 1
    else:
        visited_urls[base_url] = 1

    # mark as trap if visited too frequently
    if visited_urls[base_url] > 3:  # change number later maybe
        return True

    # # avoid long URLs with repetitive patterns
    # if len(parsed.path) > 100 or re.search(r"(\/[^\/]+){5,}", parsed.path): 
    #     return True

    return False