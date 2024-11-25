import os
import sqlite3
from datetime import datetime

from typing import List, Dict


class SqliteLogsManager:
    def __init__(self) -> None:
        self.path_db = "./src/DB/sqlite.db"
        # Asegúrate de que el archivo de base de datos esté accesible
        if not os.path.exists(self.path_db):
            os.makedirs(os.path.dirname(self.path_db), exist_ok=True)
        # Connecting with the DB
        self.sqlite_conn = sqlite3.connect(self.path_db, check_same_thread=False)
        self.sqlite_cursor = self.sqlite_conn.cursor()
        # Creating the logs table
        self._create_logs_table()
        
    def _create_logs_table(self) -> None:
        """Creates the 'logs' table, if it doesn't exists"""
        query = """CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        model TEXT,
                        input_data TEXT,
                        prediction INTEGER
                    )"""
        self.sqlite_cursor.execute(query)
        self.sqlite_conn.commit()
    
    async def save_log(self, model: str, input_data: dict, prediction: int) -> None:
        """Saves a log into SQlite
        Args:
            model (str): Name of the model
            input_data (dict): Input Data
            prediction (int): Prediction from the model
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sqlite_cursor.execute(
            "INSERT INTO logs (timestamp, model, input_data, prediction) VALUES (?, ?, ?, ?)",
            (timestamp, model, str(input_data), int(prediction))
        )
        self.sqlite_conn.commit()
    
    async def get_logs(self, limit: int = 10) -> List[Dict]:
        """Retrieves the last n logs
        Args:
            limit (int, optional): Amount of logs to retrieve. Defaults to 10.
        Returns:
            List[Dict]: List of Dictionaries from the DB
        """
        self.sqlite_cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        rows =  self.sqlite_cursor.fetchall()
        columns = [desc[0] for desc in self.sqlite_cursor.description]
        return [dict(zip(columns, row)) for row in rows]
