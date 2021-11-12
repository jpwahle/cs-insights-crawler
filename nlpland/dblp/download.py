from nlpland.dblp.DBLPClient import DBLPClient


def download():
    print("Start DBLP downloads.")
    cache_dir = "data/cache"

    dblp_client = DBLPClient(cache_dir)

    # download current dtd
    dtd_url = dblp_client.latest_url_for_extension(".dtd")
    file_path_dtd = dblp_client.download_dtd(dtd_url)

    # download current xml
    url = dblp_client.latest_url_for_extension(".xml.gz")
    file_path_gz = dblp_client.download_xml(url)
    file_path_xml = dblp_client.unzip_xml_gz(file_path_gz)

    # download 2nd latest xml (for diff)
    url2 = dblp_client.latest_url_for_extension(".xml.gz", n=2)
    file_path_gz2 = dblp_client.download_xml(url2)
    file_path_xml2 = dblp_client.unzip_xml_gz(file_path_gz2)

    # validate against dtd (takes a few minutes)
    dblp_client.validate_xml(file_path_xml)
    dblp_client.validate_xml(file_path_xml2)

    # alternative to skip steps above (requires downloaded files)
    # file_path_xml_2 = "data/cache/dblp-2021-10-01.xml"
    # file_path_xml = "data/cache/dblp-2021-11-02.xml"

    # create diff (has encoding issue with "igrave")
    dblp_client.create_diff(file_path_xml, file_path_xml2)
