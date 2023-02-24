#!/usr/bin/env python

"""pinescript_usermanual_convert_to_pdf.py: Crawl the online manual pages and convert each to a pdf file.

Quick script.  Not for commercial intent.  Use at your own risk.

pdfkit.from_url() can fail during the conversion process.  If this happens, note the chapter number
and set START_AT_PAGE to that number (include the padded 0's).  Then run script again, it should pick up
where it left off.

__author__      = "Shane DeMorais"
__copyright__   = "Copyright 2023, Planet Earth (I think)"
"""

import logging
import pdfkit

import requests
import lxml
from bs4 import BeautifulSoup
import os
import sys
import re


class Constant:
    PINESCRIPT_MANUAL_URL = "https://www.tradingview.com/pine-script-docs/en/v5/index.html"
    DOMAIN_NAME = "https://www.tradingview.com/pine-script-docs/en/v5/"
    START_AT_CHAPTER = ""
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'}


class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


def create_pdf_name(chapter_num, anchor):
    anchor = anchor.replace("/", "_").replace(".html", "") + ".pdf"
    chapter = f'{chapter_num:05d}_'

    pdf_name = "./chapters/" + chapter + anchor

    return pdf_name

def prune_subchapters(chapters):
    '''We're not interested in any href which contains a # as it's still 
       the same page as the main page
    '''
    ch = chapters.copy()
    for anchor in chapters:
        if "#" in anchor['href']:
            ch.remove(anchor)

    return ch

def find_chapters(start_url):
    f = requests.get(start_url, headers=Constant.HEADERS)

    soup = BeautifulSoup(f.content, 'lxml')
    chapters = soup.find('div', {
        'class': 'toctree-wrapper'
    }).find_all('a')

    chapters = prune_subchapters(chapters)
    
    logging.info(f"Chapters to download: {len(chapters)}")

    return chapters


def save_html_as_pdf(anchor, pdf_name):
    url = Constant.DOMAIN_NAME + anchor

    try:
        pdfkit.from_url(url, pdf_name)
        logging.info(f"- Downloaded {pdf_name}")

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)

        sys.exit(message)

    return pdf_name


def download_chapter(chapters):
    # do we have to start from a particular page?
    #
    download_html = False if len(Constant.START_AT_CHAPTER) > 0 else True

    chapter_num = 1
    for anchor in chapters:
        anchor = anchor['href']

        pdf_name = create_pdf_name(chapter_num, anchor)

        # Keep skipping until we match starting chapter.
        #
        if not download_html and Constant.START_AT_CHAPTER in pdf_name:
            download_html = True

        if download_html:
            logging.info(f"Downloading {pdf_name}")
            save_html_as_pdf(anchor, pdf_name)

        chapter_num += 1


def main(start_url):

    try:
        chapters = find_chapters(start_url)
        download_chapter(chapters)

    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)

        logging.exception(message)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    formatter = OneLineExceptionFormatter(
        '%(levelname)s:%(name)s: %(message)s')

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
    root.addHandler(handler)

    try:
        exit(main(Constant.PINESCRIPT_MANUAL_URL))
    except Exception as e:
        logging.exception(f"Exception in main(): {e}")
        exit(1)
