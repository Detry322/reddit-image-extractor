reddit-image-extractor
======================

Simple program to download all images from a specific subreddit.

This program works by repeatedly searching reddit for posts during a small time interval and then downloads the images that meet the criteria. We then expand or shrink the interval dynamically to make sure all posts are downloaded


Usage
-----

```
usage: extract.py [-h] [-s SCORE] [-d DAYS] [-o OUTPUT] [-t TARGET]
                  [-k COEFFICIENT]
                  subreddit

Download all images from a subreddit

positional arguments:
  subreddit             The subreddit to download

optional arguments:
  -h, --help            show this help message and exit
  -s SCORE, --score SCORE
                        The minimum number of points a picture must have
  -d DAYS, --days DAYS  The number of days in the past to search through
  -o OUTPUT, --output OUTPUT
                        The directory to download into
  -t TARGET, --target TARGET
                        (Advanced) The target number of posts to download in
                        each interval
  -k COEFFICIENT, --coefficient COEFFICIENT
                        (Advanced) The coefficient of change
```

Credits
-------

This project borrows heavily from [RedditImageGrab](https://github.com/HoverHell/RedditImageGrab), modified to work around the limits that reddit has on downloads.