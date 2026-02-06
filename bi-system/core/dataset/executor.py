import logging
from core.data_source.connector import DBConnector

logger = logging.getLogger(__name__)

class QueryExecutor:
    @staticmethod
    def execute(datasource, sql, limit=None, filters=None):
        """
        Execute SQL on datasource and return (columns, data)
        filters: list of dicts {'col': 'name', 'op': '=', 'val': 'value'}
        """
        # Clean semicolon at the end if present
        sql = sql.strip()
        if sql.endswith(';'):
            sql = sql[:-1]

        # Build WHERE clause from filters
        where_clause = ""
        if filters and isinstance(filters, list):
            conditions = []
            for f in filters:
                col = f.get('col')
                op = f.get('op')
                val = f.get('val')
                
                if not col or not op:
                    continue
                    
                # Basic SQL injection protection / quoting
                # Determine if value is number or string
                is_num = False
                try:
                    float(val)
                    is_num = True
                except (ValueError, TypeError):
                    is_num = False
                
                safe_val = str(val).replace("'", "''")
                val_str = f"{val}" if is_num else f"'{safe_val}'"
                
                if op == 'eq':
                    conditions.append(f"{col} = {val_str}")
                elif op == 'ne':
                    conditions.append(f"{col} != {val_str}")
                elif op == 'gt':
                    conditions.append(f"{col} > {val_str}")
                elif op == 'lt':
                    conditions.append(f"{col} < {val_str}")
                elif op == 'gte':
                    conditions.append(f"{col} >= {val_str}")
                elif op == 'lte':
                    conditions.append(f"{col} <= {val_str}")
                elif op == 'contains':
                    conditions.append(f"{col} LIKE '%{safe_val}%'")
                elif op == 'startswith':
                    conditions.append(f"{col} LIKE '{safe_val}%'")
                elif op == 'endswith':
                    conditions.append(f"{col} LIKE '%{safe_val}'")
                elif op == 'is_null':
                    conditions.append(f"{col} IS NULL")
                elif op == 'is_not_null':
                    conditions.append(f"{col} IS NOT NULL")
            
            if conditions:
                where_clause = " WHERE " + " AND ".join(conditions)

        # Apply wrapper with filters and limit
        # Common syntax for MySQL, PG, SQLite, Oracle (with subquery)
        # MSSQL uses TOP, different syntax
        
        if datasource.db_type == 'mssql':
             # MSSQL
            limit_part = f"TOP {limit}" if limit else ""
            sql = f"SELECT {limit_part} * FROM ({sql}) AS _wrapper_{where_clause}"
        elif datasource.db_type == 'oracle':
            # Oracle
            if limit:
                where_part = f"{where_clause} AND ROWNUM <= {limit}" if where_clause else f" WHERE ROWNUM <= {limit}"
                sql = f"SELECT * FROM ({sql}) {where_part}"
            else:
                sql = f"SELECT * FROM ({sql}) {where_clause}"
        else:
            # MySQL, PostgreSQL, SQLite
            limit_part = f" LIMIT {limit}" if limit else ""
            sql = f"SELECT * FROM ({sql}) AS _wrapper_{where_clause}{limit_part}"
        
        conn = None
        
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
            cursor.execute(sql)
            
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                data = cursor.fetchall()
                # Convert rows to lists for JSON serialization
                # Also handle potentially non-serializable objects if needed (handled by DjangoJSONEncoder usually)
                data = [list(row) for row in data]
                return columns, data
            else:
                return [], []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise e
        finally:
            if conn:
                conn.close()
