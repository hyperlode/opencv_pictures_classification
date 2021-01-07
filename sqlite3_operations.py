import logging
import random
import time

import sqlite3
from sqlite3 import Error


DATATYPE_TO_SQL_DATATYPE= {
    int:"INTEGER",
    str:"TEXT",
}

class DatabaseSqlite3Actions():
    def __init__(self, path,logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        self.conn = None
        self.create_connection(path)

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        try:
            self.conn = sqlite3.connect(db_file)
           
        except Error as e:
            self.logger.error("Error connecting database {}".format(e), exc_info = True)
    
    def create_table(self, table_name, columns_dict, primary_key_column):
        # will take the sequence of keys in order from columns_dict
        
        # columns_sql_formatted = ["{} {}".format(name,t) for name,t in columns_dict.items()]

        col_definitions = []
        for name, t in columns_dict.items():

            s = "{} {}".format(
                name,
                DATATYPE_TO_SQL_DATATYPE[t],
                )

            if name == primary_key_column:
                s+= " PRIMARY KEY"

            col_definitions.append(s)
        
        colums_sql_formatted = ",".join(col_definitions)


        sql_create_table = """CREATE TABLE IF NOT EXISTS {} ({});""".format(
            table_name,
            colums_sql_formatted,
            )

        self.execute_sql(sql_create_table)
        self.commit()

    def get_cursor(self):
        return self.conn.cursor()

    def execute_sql(self, sql, verbose=False, database_retries = 10):
        retry = database_retries

        while retry > 0:
            try:
                cur = self.get_cursor()
                cur.execute(sql)
                if retry  != database_retries:
                    self.logger.info("SQL success. after: {} retries".format(database_retries - retry))
                retry = 0
            except Exception as e:
                
                # sqlite3.OperationalError
                randomtime = random.randint(0,100)/100
                time.sleep(randomtime)
                retry -= 1
                self.logger.warning("Database error ({}) sql: {}, retries: {}".format(
                    e,
                    sql,
                    retry,
                    ))
        if verbose:
            max_chars = 1000
            self.logger.info("sql executed: {} (truncated to {} chars)".format(
                sql[:max_chars],
                max_chars,
                ))
        return cur

    def execute_sql_return_rows(self, sql, row_count=None, database_retries=10):
        # if row_count is None, return all fetched rows.
                    
        cur = self.execute_sql(sql,False,database_retries)
        data = cur.fetchall()
        if row_count is None:
            return data
        else:
            return data[:row_count]

    def commit(self):
        self.conn.commit()

    def get_all_records(self, tablename):
        sql = "SELECT * FROM {}".format(tablename)
        return self.execute_sql_return_rows(sql)

    def get_row_count(self, table_name):
        result = self.execute_sql("select count(*) from {}".format(table_name))
        row = result.fetchone()
        return row[0]

    def get_rows(self, table, limit=100):
        sql = "SELECT * FROM {} LIMIT {}".format(table, limit)
        cur = self.execute_sql(sql)
        data = cur.fetchall()
        return data

    def column_exists(self, table_name, column_name_to_test):

        table_info = self.get_table_info(table_name)

        for row in table_info:
            if column_name_to_test in row:
                return True

        return False

    def get_table_info(self, table_name):

        sql = "pragma table_info('{}')".format(
            table_name,
            )

        table_info = self.execute_sql_return_rows(sql)

        return table_info

    def add_column_to_existing_table(self, table_name, column_name, data_type, default_value):

        #  e.g. default_value = "null"

        if self.column_exists(table_name,column_name):
            self.logger.warning("{} in {} already exists. Will not add column".format(
                column_name,
                table_name,
            ))
            return 

        if data_type not in ["TEXT", "INT"]:
            self.logger.error("not yet added data type.")
            raise UnknownColumnTypeError 

        sql = "ALTER TABLE {} ADD COLUMN {} {} default {}".format(
            table_name,
            column_name,
            data_type,
            default_value,
            )
        try:
            self.execute_sql(sql,False,5)
        except Exception as e:
            self.logger.error("didn't add column work. {}".format(e,),exc_info=True)

    def update_record(self, table_name, col_value_dict, commit=True):
        # UPDATE pictures SET (process_status, gender) = ("BUSY","mf") WHERE "name" = "DSC_0732.JPG"
      
        primary_key_name = col_value_dict["primary_key_name"]
        primary_key_value = col_value_dict["primary_key_value"]
        if type(primary_key_value) is str:
            primary_key_value = "'{}'".format(primary_key_value)

        cols, vals = self.column_value_dict_to_formatted(col_value_dict)

        sql = ''' UPDATE {} SET ({}) = ({})
                        WHERE {} = {};'''.format(
            table_name,
            ",".join(cols),
            ",".join(vals),
            primary_key_name,
            primary_key_value,
            )

        self.execute_sql(sql)

        if commit:
            self.commit()

    def column_value_dict_to_formatted(self, col_value_dict):
        cols = []
        vals = []
        for col, val in col_value_dict.items():
            if col not in ["primary_key_name", "primary_key_value"]:
                cols.append(col)

                if type(val) is str:
                    vals.append(r'"{}"'.format(val))
                else:
                    vals.append(str(val))
        return cols, vals

    def add_record(self, table_name, col_value_dict, commit=True):

        cols, vals = self.column_value_dict_to_formatted(col_value_dict)

        sql = ''' INSERT OR IGNORE INTO {} ({})
                        VALUES ({});'''.format(
            table_name,
            ",".join(cols),
            ",".join(vals),
            )

        self.execute_sql(sql)

        if commit:
            self.commit()
    