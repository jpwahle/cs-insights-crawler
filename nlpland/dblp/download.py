from nlpland.dblp.DBLPClient import DBLPClient


def download():
    print("Start DBLP downloads.")
    cache_dir = "data/cache"

    dblp_client = DBLPClient(cache_dir)

    # dtd_url = dblp_client.latest_url_for_extension(".dtd")
    # file_path_dtd = dblp_client.download_dtd(dtd_url)
    #
    # url = dblp_client.latest_url_for_extension(".xml.gz")
    # file_path_gz = dblp_client.download_xml(url)
    # file_path_xml = dblp_client.unzip_xml_gz(file_path_gz)

    file_path_xml_2 = "data/cache/dblp-2021-10-01.xml"
    file_path_xml = "data/cache/dblp-2021-11-02.xml"

    # file_path_xml = "data/cache/1991.iwpt.xml"
    # file_path_xml = "data/cache/dblp.xml"
    # file_path_dtd = "data/cache/dblp-2019-11-22.dtd"

    dblp_client.validate_xml(file_path_xml)

    # second_url = dblp_client.latest_url_for_extension(".xml.gz", n=2)[:-3]
    # file_path_xml_2 = f"{cache_dir}/{second_url.split('/')[-1]}"

    # dblp_client.create_diff(file_path_xml, file_path_xml_2)


