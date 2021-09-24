def sql_quote(string):
    """
    Ideally we'd use a standard library but this logic was used for
    several years when creating the (now legacy) SQL
    """
    return "'" + string.replace("'", "''") + "'"

def csv_row_to_sql(row):
    sql = "SELECT tiger_line_import(ST_GeomFromText(%s,4326), %s, %s, %s, %s, %s, %s);" % (
        sql_quote(row['geometry']),
        sql_quote(row['from']),
        sql_quote(row['to']),
        sql_quote(row['interpolation']),
        sql_quote(row['street']),
        sql_quote(row['city'] + ', ' + row['state']),
        sql_quote(row['postcode'])
    )
    return sql
