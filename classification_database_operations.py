import sqlite3
import logging
from pathlib import Path

import sqlite3_operations

DATABASE_NAME = "pictures_classified.db"

PICTURE_TABLE_NAME = "pictures"

DATATYPE_TO_SQL_DATATYPE= {
    int:"INTEGER",
    str:"TEXT",
}

PICTURES_TABLE_COLUMNS_PRIMARY_KEY = "path"
PICTURES_TABLE_COLUMNS = {
    "path":str,
    "name":str,
    "faces_count":int,
    "gender":str,
    "gender_percentage":int,
    "age_guess_min":int,
    "age_guess_max":int,
    "process_status":str,
}

OPERATION_STATUSES = ["TODO", "BUSY", "DONE"]

class ImageClassificationDatabaseOperations():
    def __init__(self, db_path, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("BoardGameArena scraper database operations. init.".format(
            ))
       
        self.db_path = db_path
        self.db = sqlite3_operations.DatabaseSqlite3Actions( db_path, self.logger)

        self.database_init()

    def database_init(self):
        self.db.create_table(
            PICTURE_TABLE_NAME,
            PICTURES_TABLE_COLUMNS,
            PICTURES_TABLE_COLUMNS_PRIMARY_KEY,
            )

    def add_directory(self, dir, extensions=["jpg","jpeg"]):

        extensions = [e.lower() for e in extensions]

        files = []
        for extension in extensions:
            files.extend (sorted(Path(dir).glob('*.{}'.format(extension))))  # all files in current directory, no directory names.

        for i, picture_path in enumerate(files):
            print("process picture: {} of {}. ({})".format(
                i,
                len(files),
                picture_path,
                ))

            picture_name = Path(picture_path).name
            record_dict = {
                "path":str(picture_path),
                "name":picture_name,
                "process_status":"TODO", 
                }
            
            self.db.add_record(PICTURE_TABLE_NAME, record_dict)
            # picture_save_path = Path(save_dir, picture_name)
            # age_and_gender_from_picture(picture_path, age_net, gender_net, display=False, save_path=picture_save_path)

    def update_record(self, data ):
        # gender, gender_value, age_guess_min, age_guess_max
        self.db.update_record( PICTURE_TABLE_NAME  , data)

    def get_records_by_status(self, primary_key_name, column_names, count=None, status=None):

        return self.db.get_records_by_status(
            PICTURE_TABLE_NAME,
            primary_key_name,
            column_names,
            "process_status",
            count=count,
            status=status,
            )

    def set_status_of_record(self, primary_key_name, primary_keys, status="BUSY"):
        self.db.set_status_of_record(
            PICTURE_TABLE_NAME,
            primary_key_name,
            primary_keys,
            "process_status",
            status=status,
            )

    def get_records_by_status_and_change_status(self, find_status, set_status, count=None):
        return self.db.get_records_by_status_and_change_status(
            PICTURE_TABLE_NAME, 
            "path",
            ["path", "name"],
            "process_status",
            find_status,
            set_status,
            count=count
            )

    def reset_busy_to_todo_all_records(self):
        self.get_records_by_status_and_change_status("BUSY", "TODO")