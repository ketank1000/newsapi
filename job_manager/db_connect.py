######################################################################################################
## Contains class and functions
## Classes   : Connect_Database
##             Connect_ssh
## Functions : logging_data
##             email_notification
##
######################################################################################################

import MySQLdb

class Database:
    """
    DB connection object
    """
    global _db_connection
    global _db_cur

    def __init__(self):
        """
        Contructor creates connection object and cursor
        """
        self._db_connection = MySQLdb.connect('localhost', 'root', '', 'news')
        self._db_cur = self._db_connection.cursor()

    def query(self, query ):
        """
        input required : query
        function:
            - executes query through cursor object
            - commits the data
            - returns the commited data in bunch
        """
        result = self._db_cur.execute(query)
        self._db_connection.commit()
        return self._db_cur.fetchall()

    def query_fetchone(self, query ):
        """
        input required : query
        function:
            - executes query through cursor object
            - commits the data
            - returns the commited data (a single row)
        """
        result = self._db_cur.execute(query)
        self._db_connection.commit()
        return self._db_cur.fetchone()

    def get_all_article_url(self):
        """
        Gives list all the article urls form News and failed_new table
        this is used to find the news which are newly added
        and skip the one which are already there
        saves lot of time
        """

        tables = ['News', 'failed_news']
        all_articles = []

        for table in tables:
            query_string = "SELECT URL FROM " + table
            self._db_cur.execute(query_string)
            rows = self._db_cur.fetchall()

            for row in rows:
                all_articles.append(row[0])

        return all_articles


    def __del__(self):
        self._db_connection.close()

