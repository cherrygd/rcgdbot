import mysql.connector

class Database(mysql.connector):
    def __init__(self, _host, _user, _password, _port, _name):
        self._host = _host
        self._user = _user
        self._password = _password
        self._port = _port
        self._name = _name



    def connect(self):
        connection = mysql.connector.connect(
            host=self._host,
            port=self._port,
            database=self._name,
            user=self._user,
            password=self._password
        )

        return connection