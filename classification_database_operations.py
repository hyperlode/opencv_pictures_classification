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

    def get_record_by_status(self, primary_key_name, column_names, count=None, status=None):
        # if count=None --> all
        # if status=None --> no status needed.
        # primary_key_name name --> will be separate key in output dict
        # columns_names = list with requested columns (include primary_key_name)

        if status not in OPERATION_STATUSES:
            self.logger.error("Illegal status {}".format(status))
            return

        column_names_sql = ",".join(column_names)

        sql = "SELECT {} FROM {} WHERE {} = '{}'".format(
            column_names_sql,
            PICTURE_TABLE_NAME,
            "process_status",
            status,
            )
        rows = self.db.execute_sql_return_rows(sql,count)

        row_dicts = []
        for row in rows:
            d = {}
            for colname,v in zip(column_names, row):
                d[colname] = v

                if colname == primary_key_name:
                    d["primary_key_value"] = v
            
            d["primary_key_name"] = primary_key_name

            row_dicts.append(d)

        return row_dicts

    def set_status_of_record(self, primary_key_name, primary_keys, status="BUSY"):

        if status not in OPERATION_STATUSES:
            self.logger.error("Illegal status {}".format(status))
            return
        
        # set statuses as one sql transaction
        ids_prepared = []
        for k in primary_keys:
            if type(k) is str:
                ids_prepared.append("'{}'".format(k))
            else:
                ids_prepared.append(k)
        
        ids_formatted = ",".join(ids_prepared)

        sql = "UPDATE '{}' SET {} = '{}' WHERE  {} in ({})".format(
            PICTURE_TABLE_NAME,
            "process_status",
            status,
            primary_key_name,
            ids_formatted,
            )

        self.logger.info(sql)

        self.db.execute_sql(sql)
        self.db.commit()    

    def get_records_by_status_and_change_status(self, find_status, set_status, count=None):
        primary_key_name = "path"
        requested_columns = ["path","name"]
        records = self.get_record_by_status(primary_key_name, requested_columns, status=find_status, count=count)
        primary_key_values = [p["primary_key_value"] for p in records ]
        self.set_status_of_record(primary_key_name, primary_key_values, set_status)
        
        return records

    def database_check_if_processed():

        pass

    def database_add_results(self, primary_key_name, result_dict):

        pass
        