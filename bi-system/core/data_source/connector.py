import pyodbc
import pymysql
import psycopg2
import oracledb
import logging

logger = logging.getLogger(__name__)

class DBConnector:
    @staticmethod
    def get_connection(db_type, host, port, db_name, username, password):
        """
        Factory method to get DB connection
        """
        if db_type == 'mssql':
            try:
                # Try to find available driver
                drivers = pyodbc.drivers()
                driver = '{ODBC Driver 17 for SQL Server}'
                
                # Fallback to SQL Server if ODBC 17 not found (though less likely on modern Windows)
                if 'ODBC Driver 17 for SQL Server' not in drivers:
                    if 'SQL Server' in drivers:
                        driver = '{SQL Server}'
                    elif drivers:
                        # Use the first available one that looks like SQL Server
                        for d in drivers:
                            if 'SQL Server' in d:
                                driver = f'{{{d}}}'
                                break
                
                conn_str = f'DRIVER={driver};SERVER={host},{port};DATABASE={db_name};UID={username};PWD={password}'
                # timeout in seconds
                conn = pyodbc.connect(conn_str, timeout=10)
                return conn
            except Exception as e:
                logger.error(f"Failed to connect to MSSQL: {e}")
                raise e
        
        elif db_type == 'mysql':
            try:
                conn = pymysql.connect(
                    host=host,
                    port=int(port),
                    user=username,
                    password=password,
                    database=db_name,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                return conn
            except Exception as e:
                logger.error(f"Failed to connect to MySQL: {e}")
                raise e

        elif db_type == 'postgresql':
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=db_name,
                    user=username,
                    password=password
                )
                return conn
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise e

        elif db_type == 'oracle':
            try:
                # Construct DSN (Data Source Name)
                dsn = f"{host}:{port}/{db_name}"
                conn = oracledb.connect(
                    user=username,
                    password=password,
                    dsn=dsn
                )
                return conn
            except Exception as e:
                logger.error(f"Failed to connect to Oracle: {e}")
                raise e

        else:
            raise NotImplementedError(f"Database type {db_type} not supported yet.")

    @staticmethod
    def test_connection(datasource):
        conn = None
        try:
            conn = DBConnector.get_connection(
                datasource.db_type,
                datasource.host,
                datasource.port,
                datasource.db_name,
                datasource.username,
                datasource.password
            )
            cursor = conn.cursor()
            
            # Different validation queries for different DBs
            if datasource.db_type == 'oracle':
                cursor.execute("SELECT 1 FROM DUAL")
            else:
                cursor.execute("SELECT 1")
                
            cursor.fetchone()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
        finally:
            if conn:
                conn.close()
