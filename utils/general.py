import requests
from typing import List
from databricks.sdk import WorkspaceClient

############### Utils #############
def clean_path_for_native_python(path: str) -> str:
    return "/dbfs/" + path.lstrip("/").replace("dbfs", "").lstrip(":").lstrip("/")


def make_dir_for_file_path(dbutils, path: str):
    path_dir = "/".join(path.split("/")[:-1])
    dbutils.fs.mkdirs(path_dir)


def directory_not_empty(dbutils, path: str) -> bool:
    return len(dbutils.fs.ls(path)) > 0


def add_remote_file_to_dbfs(dbutils, file_url: str, dbfs_path: str) -> bool:
    # Read file from remote
    response = requests.get(file_url, stream=True)

    # Write file
    make_dir_for_file_path(dbutils, dbfs_path)
    with open(clean_path_for_native_python(dbfs_path), "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # Ensure write
    return directory_not_empty(dbutils, dbfs_path)



################## DBFS Writes ####################
def _add_benchmark_kit_jar_to_dbfs(dbutils, dbfs_path: str):
    return add_remote_file_to_dbfs(
        dbutils=dbutils,
        file_url="https://github.com/BlueGranite/tpc-ds-dataset-generator/blob/master/lib/spark-sql-perf_2.12-0.5.1-SNAPSHOT.jar?raw=true",
        dbfs_path=dbfs_path,
    )


def _add_init_script_to_dbfs(dbutils, init_script_path: str, jar_path: str) -> bool:
    """
    Create the BASH init script that will install the Databricks TPC-DS benchmark kit and prequisites.
    Note that this also installs the spark-sql-perf library jar.
    """
    make_dir_for_file_path(dbutils, init_script_path)

    dbutils.fs.put(
        init_script_path,
        f"""
      #!/bin/bash
      sudo apt-get --assume-yes install gcc make flex bison byacc git

      cd /usr/local/bin
      git clone https://github.com/databricks/tpcds-kit.git
      cd tpcds-kit/tools
      make OS=LINUX

      cp {jar_path.replace('dbfs:','/dbfs')} /databricks/jars/
    """,
        True,
    )

    return directory_not_empty(dbutils, init_script_path)


def _add_beaker_whl_to_dbfs(dbutils, dbfs_path) -> bool:
    return add_remote_file_to_dbfs(
        dbutils=dbutils,
        file_url="https://github.com/anhhchu/beaker/blob/main/dist/beaker-0.0.5-py3-none-any.whl",
        dbfs_path=dbfs_path,
    )


############# Main #################
def setup_files(dbutils, jar_path: str, init_script_path: str, beaker_whl_path: str):
    # jar_created = _add_benchmark_kit_jar_to_dbfs(dbutils, jar_path)
    # assert (
    #     jar_created
    # ), f"The jar path '{jar_path}' is empty. There was an error uploading it."

    init_script_created = _add_init_script_to_dbfs(dbutils, init_script_path, jar_path)
    assert (
        init_script_path
    ), f"The init script path '{init_script}' is empty. There was an error uploading it."

    beaker_whl_created = _add_beaker_whl_to_dbfs(dbutils, beaker_whl_path)
    assert (
        beaker_whl_created
    ), f"The init script path '{beaker_whl_path}' is empty. There was an error uploading it."