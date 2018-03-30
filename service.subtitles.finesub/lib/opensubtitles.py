# -*- coding: utf-8 -*

import os
from bs4 import BeautifulSoup
import requests
import hash_video
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

UA = "FineSub"

class OpenSubtitles:
    search_url = "https://rest.opensubtitles.org/search"
    expected_language = "Chinese"


    def __init__(self, movie_path):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})

        self.movie_path = movie_path
        self.movie_size, self.movie_hash = hash_video.calc_file_hash(self.movie_path)

        self.timeout = 10

    def movie_info(self):
        url = "%s/moviebytesize-%s/moviehash-%s" % (self.search_url, self.movie_size, self.movie_hash)
        try:
            infos = self.session.get(url, verify=False, timeout=self.timeout).json()
            if isinstance(infos, list) and len(infos):
                for info in infos:
                    if info["LanguageName"] == self.expected_language:
                        return info
                return infos[0]
        except Exception as e:
            # TODO
            raise e


if __name__ == '__main__':
    pass

