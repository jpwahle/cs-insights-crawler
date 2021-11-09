from nlpland.dblp.DBLPClient import DBLPClient


def download():
    cache_dir = "data/cache"

    dblp_client = DBLPClient(cache_dir)

    dtd_url = dblp_client.latest_url_for_extension(".dtd")
    dblp_client.download_dtd(dtd_url)

    url = dblp_client.latest_url_for_extension(".xml.gz")
    file_path = dblp_client.download_xml(url)
    dblp_client.unzip_xml_gz(file_path)
