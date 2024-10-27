from influxdb import InfluxDBClient
import pandas as pd

client = InfluxDBClient(host='localhost', port=0000, username='user', password='pass', database='db')

query = """
SELECT build_number, rf_failed, rf_name, rf_passed, rf_suite_name
FROM testcase_point
WHERE project_name='ETSc2-Robot-Tests' AND time > now() - 120d
"""

result = client.query(query)
# Drops "time" column
df = pd.DataFrame(result.get_points()).drop(columns=['time'])
df.to_csv('testcase_data_csv.csv', index=False)
