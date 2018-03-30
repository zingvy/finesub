# -*- coding: utf-8 -*

import os
from bs4 import BeautifulSoup
import requests
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

TIMEOUT = 10

class Zimuku:
    domain = "https://www.zimuku.cn"
    dld_url = "http://www.subku.net/dld/%s.html"


    def __init__(self, search_str):
        self.search_url = "%s/search?q=%s" % (self.domain, search_str)
        self.session = requests.Session()

    def get_subid_from_href(self, href):
        return os.path.basename(href).split(".")[0]

    def fetch_movie_uri(self):
        data = self.session.get(self.search_url, verify=False, timeout=TIMEOUT).text
        soup = BeautifulSoup(data, "html.parser")
        title_div = soup.find('div', {"class":"title"})
        link = title_div.find("a")
        return link.get('href')

    def fetch_subs_list(self):
        url = "%s%s" % (self.domain, self.fetch_movie_uri())
        data = self.session.get(url, verify=False, timeout=TIMEOUT).text
        soup = BeautifulSoup(data, 'html.parser').find("div", class_="subs box clearfix")
        subs = soup.tbody.find_all("tr")
        subtitles_list = []
        for sub in subs:
            subid = self.get_subid_from_href(sub.a.get('href').encode('utf-8'))
            link = self.get_dld_url(subid)

            version = sub.a.text.encode('utf-8')
            try:
                td = sub.find("td", class_="tac lang")
                r2 = td.find_all("img")
                langs = [x.get('title').encode('utf-8') for x in r2]
            except:
                langs = '未知'
            name = '%s (%s)' % (version, ",".join(langs))
            rating = "0"
            try:
                r = sub.find("i", class_="rating-star")
                rating = r.get("title").encode("utf-8")
            except:
                pass
            rating = "0"
            if ('English' in langs) and not(('简体中文' in langs) or ('繁體中文' in langs)):
                subtitles_list.append({"language_name":"English", "filename":name, "link":link, "language_flag":'en', "rating":rating, "lang":langs, "referer": self.dld_url % subid})
            else:
                subtitles_list.append({"language_name":"Chinese", "filename":name, "link":link, "language_flag":'zh', "rating":rating, "lang":langs, "referer": self.dld_url % subid})
        return subtitles_list

    def get_dld_url(self, subid):
        url = self.dld_url % subid
        data = self.session.get(url, timeout=TIMEOUT).text
        soup = BeautifulSoup(data, "html.parser")
        for link in soup.find_all("a", {"class":"btn-sm"}):
            return link.get("href")

    def download_subtitle(self, sub_id, url):
        self.session.headers["Referer"] = dld_url % sub_id
        data = self.session.get(url)
        with open("%s.srt"% sub_id, "wb") as f:
            f.write(data.content)
        return True
