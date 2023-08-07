import snowflake.connector

snowflake.connector.paramstyle = 'qmark'
snowflake_conn = snowflake.connector.connect(
    user='glenn',
    password='SFRsfrsfr665!',
    account='xdb39708',
    database='GLENN_WORKING',
    schema='PUBLIC',
    region='us-west-2',
    client_session_keep_alive=True
)
