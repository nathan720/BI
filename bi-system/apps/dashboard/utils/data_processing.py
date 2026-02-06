import pandas as pd

def aggregate_data(data, x_col, y_cols, agg_type, series_col=None):
    """
    Aggregates data based on x_col and agg_type.
    :param data: List of dicts
    :param x_col: Group by column
    :param y_cols: List of value columns or single string
    :param agg_type: 'sum', 'mean', 'max', 'min', 'count'
    :param series_col: Optional series column for pivoting
    :return: List of dicts (aggregated)
    """
    if not data or not x_col or not agg_type or agg_type == 'none':
        return data

    try:
        df = pd.DataFrame(data)
        
        # Ensure cols exist
        if x_col not in df.columns:
            return data
            
        if isinstance(y_cols, str):
            y_cols = [y_cols]
        
        # Deduplicate y_cols to avoid DataFrame column name conflicts
        y_cols = list(dict.fromkeys(y_cols))
        
        valid_y_cols = [c for c in y_cols if c in df.columns]
        if not valid_y_cols:
            return data

        # Convert Y cols to numeric
        for col in valid_y_cols:
            # Handle string numbers with commas
            if df[col].dtype == 'object':
                 df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Grouping
        group_cols = [x_col]
        if series_col and series_col in df.columns:
            group_cols.append(series_col)

        if agg_type == 'sum':
            df_agg = df.groupby(group_cols)[valid_y_cols].sum().reset_index()
        elif agg_type == 'mean':
            df_agg = df.groupby(group_cols)[valid_y_cols].mean().reset_index()
        elif agg_type == 'max':
            df_agg = df.groupby(group_cols)[valid_y_cols].max().reset_index()
        elif agg_type == 'min':
            df_agg = df.groupby(group_cols)[valid_y_cols].min().reset_index()
        elif agg_type == 'count':
            df_agg = df.groupby(group_cols)[valid_y_cols].count().reset_index()
        else:
            return data
            
        return df_agg.to_dict('records')
    except Exception as e:
        print(f"Aggregation error: {e}")
        return data
