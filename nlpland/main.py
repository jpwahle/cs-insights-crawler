import os
import pandas as pd






# def df_create_cols(df: pd.DataFrame) -> None:
#     if ABSTRACT_COLUMN not in df.columns:
#         df[ABSTRACT_COLUMN] = None
#     if UNICODE_COLUMN not in df.columns:
#         df[UNICODE_COLUMN] = False
#     if ABSTRACT_SOURCE_COLUMN not in df.columns:
#         df[ABSTRACT_SOURCE_COLUMN] = None









if __name__ == '__main__':
    df_main = pd.read_csv(os.getenv("PATH_DATASET"), delimiter="\t", low_memory=False, header=0, index_col=0)
    df_expanded = pd.read_csv(os.getenv("PATH_DATASET_EXPANDED"), delimiter="\t", low_memory=False, header=0, index_col=0)
    # analyse_dataset(df_expanded)
    # check_paper_text()
    # download_papers(df_main, 1965, 2020)
    # extract_abstracts(df_main, False)
    top_tier = ["ACL", "EMNLP", "NAACL", "COLING", "EACL"]
    # top_tier = ["COLING"]
    # top_tier = None
    # extract_abstracts(df_expanded, min_year=2010, venues=top_tier, overwrite_abstracts=False)
    # paper_stats(df_main)
    # print_unicode_to_file(df_expanded)
    extract_abstracts_anthology(df_main)

    # runner = CliRunner()
    # result = runner.invoke(my_command)
    # traceback.print_exception(*result.exc_info)