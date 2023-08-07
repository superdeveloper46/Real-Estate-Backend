from flask import Blueprint, g, make_response, jsonify, request, json

from appname.models import db

from datetime import date

from appname.controllers.privateLenders.snowflake import snowflake_conn

lenders = Blueprint('lenders', __name__)

@lenders.route("/api/lenders/getArea", methods=["GET"])
def getArea():
    cursor = snowflake_conn.cursor()
    query = f"""
    select msa, count(*)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%'
    group by 1
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getLenderName", methods=["GET"])
def getLenderName():
    cursor = snowflake_conn.cursor()
    query = f"""
    select lender, count(*)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and multi_apn is null
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    group by 1
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getTopLenders/<string:param>", methods=["GET"])
def getTopLenders(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and msa = '{param}'
    and multi_apn is null
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), quarterly_stats as (
    select date_trunc('quarter', recording_date), 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*), sum(first_mtg_amt),
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select lender, count(*) as num_originations, sum(first_mtg_amt) as origination_volume, sum(first_mtg_amt)/count(*) as avg_origination_sixe --, listagg(distinct lender, ',')
    from base b 
    group by 1
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getLoanOriginations/<string:param>", methods=["GET"])
def getLoanOriginations(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    --num borrowers; largest lenders; 25,50,75 metrics, avg orig size, num orig; largest borrowers
    --MSA MONTHLY ANALYSIS
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and msa = '{param}'
    and multi_apn is null
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), monthly_stats as (
    select date_trunc('month', recording_date) as month, 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*) as num_loans, sum(first_mtg_amt) as origination_volume,
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select * from monthly_stats
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getBorrowerList/<string:param>", methods=["GET"])
def getBorrowerList(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    --num borrowers; largest lenders; 25,50,75 metrics, avg orig size, num orig; largest borrowers
    --MSA MONTHLY ANALYSIS
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and lender = '{param}'
    and multi_apn is null
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), quarterly_stats as (
    select date_trunc('quarter', recording_date), 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*), sum(first_mtg_amt),
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select buyer_borrower1_name, count(*)
    from base 
    group by 1 
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getOriginationStatsTable/<string:param>", methods=["GET"])
def getOriginationStatsTable(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    --num borrowers; largest lenders; 25,50,75 metrics, avg orig size, num orig; largest borrowers
    --MSA MONTHLY ANALYSIS
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and lender = '{param}'
    and multi_apn is null
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), quarterly_stats as (
    select date_trunc('quarter', recording_date), 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*), sum(first_mtg_amt),
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select msa, count(*)
    from base 
    group by 1 
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getOriginationStatsChart/<string:param>", methods=["GET"])
def getOriginationStatsChart(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    --num borrowers; largest lenders; 25,50,75 metrics, avg orig size, num orig; largest borrowers
    --MSA MONTHLY ANALYSIS
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and lender = '{param}'
    and multi_apn is null
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), quarterly_stats as (
    select date_trunc('quarter', recording_date), 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*), sum(first_mtg_amt),
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select date_trunc('month', recording_date) as month, count(*)
    from base 
    group by 1 
    order by 1 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getOriginationVolume/<string:param>", methods=["GET"])
def getOriginationVolume(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    --num borrowers; largest lenders; 25,50,75 metrics, avg orig size, num orig; largest borrowers
    --MSA MONTHLY ANALYSIS
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and lender = '{param}'
    and multi_apn is null
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), quarterly_stats as (
    select date_trunc('quarter', recording_date), 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*), sum(first_mtg_amt),
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select date_trunc('month', recording_date) as month, sum(first_mtg_amt)
    from base 
    group by 1 
    order by 1 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getBorrowersWent/<string:param>", methods=["GET"])
def getBorrowersWent(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    WITH buyer_lender_dates AS (
    SELECT buyer_borrower1_name, lender, MIN(recording_date) AS min_recording_date, MAX(recording_date) AS max_recording_date
    FROM deeds_2022_plus d
    JOIN private_lender_list_clean c ON c.first_mtg_lender_name = d.first_mtg_lender_name
    WHERE recording_date >= '2022-01-01'
    AND land_use_code IN (1001, 1000, 1999)
    AND c.lender != 'German American Capital'
    AND c.lender != 'Goldman Sachs'
    AND c.lender != 'BAKER STREET MORTGAGE HOLDINGS'
    AND c.lender != 'SFR MANAGING BORROWER LLC'
    AND c.lender != 'Deephaven'
    AND multi_apn IS NULL
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
        AND ((transaction_type = 2 AND (fa_transaction_id ILIKE '1%' OR fa_transaction_id ILIKE '6%')) OR 
        (transaction_type = 2 AND (fa_transaction_id ILIKE '2%' OR fa_transaction_id ILIKE '7%')))
        AND (d.first_mtg_amt / NULLIF(current_avm_value, 0) < 2 OR current_avm_value < 1000000)
        AND d.first_mtg_amt / NULLIF(current_avm_value, 0) < 3
        GROUP BY buyer_borrower1_name, lender
    ),

    new_lender_data AS (
        SELECT bl1.buyer_borrower1_name, bl1.lender AS old_lender, bl2.lender AS new_lender, bl1.min_recording_date,
        bl1.max_recording_date,bl2.min_recording_date as new_min,bl2.max_recording_date as new_max
        --ROW_NUMBER() OVER (PARTITION BY bl1.buyer_borrower1_name, bl1.lender ORDER BY bl2.min_recording_date) AS rn
        FROM buyer_lender_dates bl1
        JOIN buyer_lender_dates bl2 ON bl1.buyer_borrower1_name = bl2.buyer_borrower1_name AND bl1.lender != bl2.lender 
    )

    select distinct buyer_borrower1_name, listagg(new_lender, ' | ') as new_lenders
    from new_lender_data
    where new_max > max_recording_date
    and new_min >= '2023-01-01'
    and old_lender = '{param}'
    group by 1
    order by 1 ASc, 2 asc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getNewBorrowers/<string:param>", methods=["GET"])
def getNewBorrowers(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    WITH buyer_lender_dates AS (
    SELECT buyer_borrower1_name, lender, MIN(recording_date) AS min_recording_date, MAX(recording_date) AS max_recording_date
    FROM deeds_2022_plus d
    JOIN private_lender_list_clean c ON c.first_mtg_lender_name = d.first_mtg_lender_name
    WHERE recording_date >= '2022-01-01'
    AND land_use_code IN (1001, 1000, 1999)
    AND c.lender != 'German American Capital'
    AND c.lender != 'Goldman Sachs'
    AND c.lender != 'BAKER STREET MORTGAGE HOLDINGS'
    AND c.lender != 'SFR MANAGING BORROWER LLC'
    AND c.lender != 'Deephaven'
    AND multi_apn IS NULL
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
        AND ((transaction_type = 2 AND (fa_transaction_id ILIKE '1%' OR fa_transaction_id ILIKE '6%')) OR 
        (transaction_type = 2 AND (fa_transaction_id ILIKE '2%' OR fa_transaction_id ILIKE '7%')))
        AND (d.first_mtg_amt / NULLIF(current_avm_value, 0) < 2 OR current_avm_value < 1000000)
        AND d.first_mtg_amt / NULLIF(current_avm_value, 0) < 3
        GROUP BY buyer_borrower1_name, lender
    ),

    new_lender_data AS (
        SELECT bl1.buyer_borrower1_name, bl1.lender AS old_lender, bl2.lender AS new_lender, bl1.min_recording_date,
        bl1.max_recording_date,bl2.min_recording_date as new_min,bl2.max_recording_date as new_max
        --ROW_NUMBER() OVER (PARTITION BY bl1.buyer_borrower1_name, bl1.lender ORDER BY bl2.min_recording_date) AS rn
        FROM buyer_lender_dates bl1
        JOIN buyer_lender_dates bl2 ON bl1.buyer_borrower1_name = bl2.buyer_borrower1_name AND bl1.lender != bl2.lender 
    )

    select distinct buyer_borrower1_name, listagg(old_lender, ' | ') as old_lenders
    from new_lender_data
    where new_max > max_recording_date
    and new_min >= '2023-01-01'
    and new_lender = '{param}'
    group by 1
    order by 1 ASc, 2 asc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getTransactionList/<string:param>", methods=["GET"])
def getTransactionList(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    --num borrowers; largest lenders; 25,50,75 metrics, avg orig size, num orig; largest borrowers
    --MSA MONTHLY ANALYSIS
    with base as (
    select *, d.first_mtg_amt/nullif(current_avm_value,0)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and lender = '{param}'
    and multi_apn is null
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    --and msa ilike '%akron%'
    order by recording_date desc
    ), quarterly_stats as (
    select date_trunc('quarter', recording_date), 
    -- percentile_cont(0.25) within group(order by first_mtg_amt) over () as p25,
    --  percentile_cont(0.50) within group(order by first_mtg_amt) over () as p50,
    --  percentile_cont(0.75) within group(order by first_mtg_amt) over () as p75, 
    count(*), sum(first_mtg_amt),
    sum(first_mtg_amt)/count(*), count(distinct buyer_borrower1_name)
    from base 
    group by 1--,2,3,4
    order by 1 desc
    )
    select *
    from base 
    order by recording_date desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getBuyers", methods=["GET"])
def getBuyers():
    cursor = snowflake_conn.cursor()
    query = f"""
    select buyer_borrower1_name, count(*)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and multi_apn is null
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    group by 1
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getLenders/<string:param>", methods=["GET"])
def getLenders(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    select lender, count(*)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and multi_apn is null
    and buyer_borrower1_name = '{param}'
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    group by 1
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getLendersOverTime/<string:param>", methods=["GET"])
def getLendersOverTime(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    select lender, date_trunc('month', recording_date) as month, count(*)
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and multi_apn is null
    and buyer_borrower1_name = '{param}'
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    group by 1,2
    order by 2 desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

@lenders.route("/api/lenders/getBuyerTransactionList/<string:param>", methods=["GET"])
def getBuyerTransactionList(param):
    cursor = snowflake_conn.cursor()
    query = f"""
    select *
    from deeds_2022_plus d 
    join private_lender_list_clean c on c.first_mtg_lender_name = d.first_mtg_lender_name
    where 
    --c.lender ilike 'LEGACY GROUP CAPITAL LLC%'
    recording_date >= '2022-01-01'
    and land_use_code in (1001,1000,1999)
    and lender != 'German American Capital'
    and lender != 'Goldman Sachs'
    and lender != 'Deephaven'
    and multi_apn is null
    and buyer_borrower1_name = '{param}'
    and ((transaction_type = 2 and ( fa_transaction_id ilike '1%' or fa_transaction_id ilike '6%')) or 
    (transaction_type = 2 and ( fa_transaction_id ilike '2%' or fa_transaction_id ilike '7%')))
    and ( d.first_mtg_amt/nullif(current_avm_value,0) < 2 or current_avm_value < 1000000)
    and d.first_mtg_amt/nullif(current_avm_value,0) <3
    -- and 
    and (msa ilike '%jacksonville, fl%'
    or msa ilike '%austin%'
    or msa ilike '%san diego%')
    order by recording_date desc
    """
    cursor.execute(query)
    areaData = cursor.fetchall()
    
    result = json.dumps([data for data in areaData])
    return make_response(result, 200)

