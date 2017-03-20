import argparse
import time
import datetime
import json
import os
from urllib import urlencode
from urllib2 import urlopen, HTTPError, URLError

def parse_args():
    parser = argparse.ArgumentParser(description="Download all images from a subreddit")
    parser.add_argument('subreddit', help="The subreddit to download")
    parser.add_argument('-s', '--score', help='The minimum number of points a picture must have', type=int, default=0)
    parser.add_argument('-d', '--days', help="The number of days in the past to search through", type=int, default=365)
    parser.add_argument('-o', '--output', help="The directory to download into", type=str, default='downloads')
    parser.add_argument('-t', '--target', help="(Advanced) The target number of posts to download in each interval", type=int, default=20)
    parser.add_argument('-k', '--coefficient', help="(Advanced) The coefficient of change", type=float, default=2.0)
    return parser.parse_args()

def get_secs(t):
    return int(time.mktime(t.timetuple()))

def request(url, *ar, **kwa):
    _retries = kwa.pop('_retries', 4)
    _retry_pause = kwa.pop('_retry_pause', 0)
    res = None
    for _try in xrange(_retries):
        try:
            res = urlopen(url, *ar, **kwa)
        except Exception as exc:
            if _try == _retries - 1:
                return None
            print("Try %r err %r  (%r)" % (
                _try, exc, url))
        else:
            break
    return res

def do_search(subreddit, start, end):
    url = "https://reddit.com/{}/search.json?q=timestamp:{}..{}&sort=top&restrict_sr=on&syntax=cloudsearch".format(subreddit, get_secs(start), get_secs(end))
    try:
        r = request(url)
        if r is None:
            return []
        data = json.loads(r.read())
        return data["data"]["children"] 
    except ValueError:
        return []


def extract_imgur_album_urls(album_url):
    response = request(album_url)
    if not response:
        return []
    info = response.info()

    # Rudimentary check to ensure the URL actually specifies an HTML file
    if 'content-type' in info and not info['content-type'].startswith('text/html'):
        return []

    filedata = response.read()
    # TODO: stop parsing HTML with regexes.
    match = re.compile(r'\"hash\":\"(.[^\"]*)\",\"title\"')
    items = []

    memfile = StringIO.StringIO(filedata)

    for line in memfile.readlines():
        results = re.findall(match, line)
        if not results:
            continue

        items += results

    memfile.close()
    # TODO : url may contain gif image.
    urls = ['http://i.imgur.com/%s.jpg' % (imghash) for imghash in items]

    return urls

def process_imgur_url(url):
    if 'imgur.com/a/' in url or 'imgur.com/gallery/' in url:
        return extract_imgur_album_urls(url)

    # Change .png to .jpg for imgur urls.
    if url.endswith('.png'):
        url = url.replace('.png', '.jpg')
    else:
        # Extract the file extension
        ext = pathsplitext(pathbasename(url))[1]
        if ext == '.gifv':
            url = url.replace('.gifv', '.gif')
        if not ext:
            # Append a default
            url += '.jpg'
    return [url]

def extract_urls(url):
    urls = []
    if 'imgur.com' in url:
        urls = process_imgur_url(url)
    else:
        urls = [url]

    return urls

def resize_interval(old_interval, matched_posts, target, coefficient):
    MAX_POSTS = 25
    if matched_posts <= target/4:
        return old_interval*(1+coefficient) # Safety
    difference = float(target - matched_posts)
    if difference > 0:
        return old_interval * ((difference/(3*target/4.0))*coefficient + 1)
    return old_interval * 1.0/(1 + coefficient/3.0*(difference/(target - MAX_POSTS)))

def find_images(subreddit, min_score, days, target, coefficient):
    end = datetime.datetime.now()
    current = end - datetime.timedelta(days=days)
    interval = 3.0
    while current < end:
        current_stop = current + datetime.timedelta(seconds=interval)
        matched_posts = 0
        for post in do_search(subreddit, current, current_stop):
            if post['data']['score'] > min_score:
                matched_posts += 1
                for url in extract_urls(post['data']['url']):
                    yield url
        print " === {} posts matched".format(matched_posts)
        interval = resize_interval(interval, matched_posts, target, coefficient)
        current = current_stop



def download_image(url, download_dir):
    if os.path.isdir(download_dir):
        os.makedirs(download_dir)

    dest_file = os.path.join(download_dir, os.urandom(10).encode('hex'))

    response = request(url)
    if not response:
        print "Error trying to download file"
        return

    info = response.info()
    actual_url = response.url
    if actual_url == 'http://i.imgur.com/removed.png':
        print "Imgur suggests the image was removed"
        return

    # Work out file type either from the response or the url.
    if 'content-type' in info.keys():
        filetype = info['content-type']
    elif url.endswith('.jpg') or url.endswith('.jpeg'):
        filetype = 'image/jpeg'
    elif url.endswith('.png'):
        filetype = 'image/png'
    elif url.endswith('.gif'):
        filetype = 'image/gif'
    else:
        filetype = 'unknown'

    # Only try to download acceptable image types
    if filetype == 'image/jpeg':
        dest_file += '.jpg'
    elif filetype == 'image/png':
        dest_file += '.png'
    elif filetype == 'image/gif':
        dest_file += '.gif'
    else:
        print 'WRONG FILE TYPE: %s has type: %s!' % (url, filetype)
        return

    filedata = response.read()
    filehandle = open(dest_file, 'wb')
    filehandle.write(filedata)
    filehandle.close()


def main():
    args = parse_args()
    for image_url in find_images(args.subreddit, args.score, args.days, args.target, args.coefficient):
        download_image(image_url, args.output)

if __name__ == "__main__":
    main()