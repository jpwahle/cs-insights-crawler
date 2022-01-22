"""This module implements a client to communicate with the grobid server.
Adjusted and typed from https://github.com/kermitt2/grobid_client_python

This version uses the standard ProcessPoolExecutor for parallelizing the
concurrent calls to the GROBID services.  Given the limits of
ThreadPoolExecutor (the legendary GIL, input stored in memory, blocking
Executor.map until the whole input is acquired), ProcessPoolExecutor works with
batches of PDF of a size indicated in the config.json file (default is 1000
entries). We are moving from first batch to the second one only when the first
is entirely processed - which means it is slightly sub-optimal, but should
scale better. Working without batch would mean acquiring a list of millions of
files in directories and would require something scalable too (e.g. done in a
separate thread), which is not implemented for the moment and possibly not
implementable in Python as long it uses the GIL.
"""
import json
import ntpath
import os
import pathlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

import requests

from nlpland.client.generic.genericclient import GenericApiClient
from nlpland.log import LogMixin
from nlpland.types import ServerUnavailableException, ValidGrobidServices

T = TypeVar("T", bound="GrobidClient")


class GrobidClient(GenericApiClient, LogMixin):
    def __init__(
        self: T,
        grobid_server: str,
        grobid_batch_size: int,
        grobid_port: Optional[int] = None,
        coordinates: List[str] = ["persName", "figure", "ref", "biblStruct", "formula", "s"],
        sleep_time: float = 5.0,
        timeout: int = 60,
        check_server: bool = True,
        config_path: Optional[Path] = None,
        **kwargs: Any,
    ):
        self.config: Dict[str, Union[str, int, Optional[int], float, List[str]]] = {
            "grobid_server": grobid_server,
            "grobid_port": grobid_port,
            "batch_size": grobid_batch_size,
            "coordinates": coordinates,
            "sleep_time": sleep_time,
            "timeout": timeout,
        }
        if config_path:
            self._load_config(config_path)
        if check_server:
            self._test_server_connection()

    def _load_config(self: T, path: Path = Path("./config.json")) -> None:
        """Load the json configuration"""
        config_json = open(path).read()
        self.config = json.loads(config_json)

    def _test_server_connection(self: T) -> None:
        """Test if the server is up and running."""
        the_url = str(self.config["grobid_server"])
        if self.config["grobid_port"]:
            the_url = f"{the_url}:{str(self.config['grobid_port'])}"
        the_url = f"{the_url}/api/isalive"
        try:
            r = requests.get(the_url)
        except requests.exceptions.ConnectionError:
            self.logger.debug(
                "GROBID server does not appear up and running, the connection to the server failed"
            )
            raise ServerUnavailableException

        status = r.status_code

        if status != 200:
            self.logger.debug("GROBID server does not appear to be up and running " + str(status))
        else:
            self.logger.debug("GROBID server is up and running")

    def _output_file_name(
        self: T, input_file: Path, input_path: Path, output: Optional[Path] = None
    ) -> Path:
        # we use ntpath here to be sure it will work on Windows too
        if output is not None:
            input_file_name = str(os.path.relpath(os.path.abspath(input_file), input_path))
            filename = Path(os.path.join(output, os.path.splitext(input_file_name)[0] + ".tei.xml"))
        else:
            input_file_name = ntpath.basename(input_file)
            filename = Path(
                os.path.join(
                    ntpath.dirname(input_file),
                    os.path.splitext(input_file_name)[0] + ".tei.xml",
                )
            )

        return filename

    def process(
        self: T,
        grobid_service: ValidGrobidServices = ValidGrobidServices.processHeaderDocument,
        input_path: Path = Path("."),
        grobid_pdf_extraction_threads: int = 10,
        grobid_generate_ids: bool = False,
        grobid_consolidate_header: bool = True,
        grobid_consolidate_citations: bool = False,
        grobid_include_raw_citations: bool = False,
        grobid_include_raw_affiliations: bool = False,
        grobid_tei_coordinates: bool = False,
        grobid_segment_sentences: bool = False,
        force: bool = False,
        output: Optional[Path] = None,
        **kwargs: Any,
    ) -> None:
        input_files = []
        batch_size_pdf = self.config["batch_size"]

        for (dirpath, _, filenames) in os.walk(input_path):
            for filename in filenames:
                if (
                    filename.endswith(".pdf")
                    or filename.endswith(".PDF")
                    or (
                        grobid_service == "processCitationList"
                        and (filename.endswith(".txt") or filename.endswith(".TXT"))
                    )
                ):
                    self.logger.debug(filename)
                    input_files.append(Path(os.sep.join([dirpath, filename])))

                    if len(input_files) == batch_size_pdf:
                        self.process_batch(
                            grobid_service,
                            input_files,
                            input_path,
                            grobid_pdf_extraction_threads,
                            grobid_generate_ids,
                            grobid_consolidate_header,
                            grobid_consolidate_citations,
                            grobid_include_raw_citations,
                            grobid_include_raw_affiliations,
                            grobid_tei_coordinates,
                            grobid_segment_sentences,
                            force,
                            output,
                        )
                        input_files = []

        # last batch
        if len(input_files) > 0:
            self.process_batch(
                grobid_service,
                input_files,
                input_path,
                grobid_pdf_extraction_threads,
                grobid_generate_ids,
                grobid_consolidate_header,
                grobid_consolidate_citations,
                grobid_include_raw_citations,
                grobid_include_raw_affiliations,
                grobid_tei_coordinates,
                grobid_segment_sentences,
                force,
                output,
            )

    def process_batch(
        self: T,
        service: ValidGrobidServices,
        input_files: List[Path],
        input_path: Path,
        n: int,
        generateIDs: bool,
        consolidate_header: bool,
        consolidate_citations: bool,
        include_raw_citations: bool,
        include_raw_affiliations: bool,
        tei_coordinates: bool,
        segment_sentences: bool,
        force: bool,
        output: Optional[Path] = None,
    ) -> None:

        # TODO: Make requests async with aiohttp

        results = []
        for input_file in input_files:
            # check if TEI file is already produced
            filename = self._output_file_name(input_file, input_path, output)
            if not force and os.path.isfile(filename):
                self.logger.debug(
                    filename,
                    "already exist, skipping... (use --force to reprocess pdf input files)",
                )
                continue

            selected_process = self.process_pdf
            if service == "processCitationList":
                selected_process = self.process_txt

            r = selected_process(
                service,
                input_file,
                generateIDs,
                consolidate_header,
                consolidate_citations,
                include_raw_citations,
                include_raw_affiliations,
                tei_coordinates,
                segment_sentences,
            )

            results.append(r)

        for r in results:
            input_file, status, text = r
            filename = self._output_file_name(input_file, input_path, output)

            if text is None:
                self.logger.debug("Processing of", input_file, "failed with error", str(status))
            else:
                # writing TEI file
                try:
                    pathlib.Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
                    with open(filename, "w", encoding="utf8") as tei_file:
                        tei_file.write(text)
                except OSError:
                    self.logger.debug("Writing resulting TEI XML file", filename, "failed")

    def process_pdf(
        self: T,
        service: ValidGrobidServices,
        file: Path,
        generateIDs: bool,
        consolidate_header: bool,
        consolidate_citations: bool,
        include_raw_citations: bool,
        include_raw_affiliations: bool,
        tei_coordinates: bool,
        segment_sentences: bool,
    ) -> Tuple[Path, int, Optional[str]]:

        files = {
            "input": (
                str(file),
                open(str(file), "rb"),
                "application/pdf",
                {"Expires": "0"},
            )
        }

        the_url = self.config["grobid_server"]
        if self.config["grobid_port"]:
            the_url = f"{the_url}:{self.config['grobid_port']}"
        the_url = f"{the_url}/api/{service}"

        # set the GROBID parameters
        the_data: Dict[str, Union[str, int, Optional[int], float, List[str]]] = {}
        if generateIDs:
            the_data["generateIDs"] = "1"
        if consolidate_header:
            the_data["consolidateHeader"] = "1"
        if consolidate_citations:
            the_data["consolidateCitations"] = "1"
        if include_raw_citations:
            the_data["includeRawCitations"] = "1"
        if include_raw_affiliations:
            the_data["includeRawAffiliations"] = "1"
        if tei_coordinates:
            the_data["teiCoordinates"] = self.config["coordinates"]
        if segment_sentences:
            the_data["segmentSentences"] = "1"

        # try:
        res, status = self.post(
            url=the_url,
            files=files,
            data=the_data,
            # headers={"Accept": "text/plain"},
            timeout=self.config["timeout"],
        )

        if status == 503:
            assert isinstance(self.config["sleep_time"], float), "sleep_time has to be a float"
            time.sleep(self.config["sleep_time"])
            return self.process_pdf(
                service,
                file,
                generateIDs,
                consolidate_header,
                consolidate_citations,
                include_raw_citations,
                include_raw_affiliations,
                tei_coordinates,
                segment_sentences,
            )
        # except requests.exceptions.ReadTimeout:
        #     return (file, 408, None)

        return (file, status, res.text)

    def process_txt(
        self: T,
        service: ValidGrobidServices,
        file: Path,
        generateIDs: bool,
        consolidate_header: bool,
        consolidate_citations: bool,
        include_raw_citations: bool,
        include_raw_affiliations: bool,
        tei_coordinates: bool,
        segment_sentences: bool,
    ) -> Tuple[Path, int, Optional[str]]:
        # create request based on file content
        references = None
        with open(file) as f:
            references = [line.rstrip() for line in f]

        the_url = "http://" + str(self.config["grobid_server"])
        if self.config["grobid_port"]:
            the_url += ":" + str(self.config["grobid_port"])
        the_url += "/api/" + service

        # set the GROBID parameters
        the_data: Dict[str, Any] = {}
        if consolidate_citations:
            the_data["consolidateCitations"] = "1"
        if include_raw_citations:
            the_data["includeRawCitations"] = "1"
        the_data["citations"] = references
        res, status = self.post(url=the_url, data=the_data, headers={"Accept": "application/xml"})

        if status == 503:
            assert isinstance(self.config["sleep_time"], float), "sleep_time has to be a float"
            time.sleep(self.config["sleep_time"])
            return self.process_txt(
                service,
                file,
                generateIDs,
                consolidate_header,
                consolidate_citations,
                include_raw_citations,
                include_raw_affiliations,
                tei_coordinates,
                segment_sentences,
            )

        return (file, status, res.text)
