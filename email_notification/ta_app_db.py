import psycopg2
import copy
from send_email_settings import *

class TaAppDatabase:
    def __init__(self, user, password, host, port, database):
        try:
            self.connection = psycopg2.connect(user=user, password=password, host=host, port=port, database=database)
            self.cursor = self.connection.cursor()

        except (Exception, psycopg2.Error) as error :
            print ("Error while connecting to PostgreSQL", error)

        finally:
            if self.connection:
                statuses = self.get_application_statuses()
                self.statuses = statuses

    def close(self):
        self.cursor.close()
        self.connection.close()

    def get_application_statuses(self):
        """ Get all application statuses """

        #self.cursor.execute("SELECT application_id, assigned_hours, created_at FROM administrators_applicationstatus WHERE assigned='" + ACCEPTED_ID + "' AND created_at >= '" + YESTERDAY + "' AND created_at < '" + TODAY + "' ORDER BY id ASC;")
        self.cursor.execute("SELECT application_id, assigned_hours, created_at FROM administrators_applicationstatus WHERE assigned='" + ACCEPTED_ID + "' AND created_at='" + TODAY + "' ORDER BY id ASC;")
        return self.cursor.fetchall()
