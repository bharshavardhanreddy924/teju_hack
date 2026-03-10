import app
import os

schema_info = 'Table name: user_data\nColumns: Impressions (REAL), Clicks (REAL)'
print('---TEST BEGIN---')
try:
    res = app.get_sql_query('hiiiii', schema_info, '')
    print('RESULT:')
    print(res)
except Exception as e:
    print('ERROR:', type(e), e)
print('---TEST END---')
