from flask import Blueprint, g, make_response, request, json, g, jsonify

from appname.models import db

from datetime import datetime, timedelta
from appname.models.user import User
from appname.controllers.privateLenders.snowflake import snowflake_conn
from appname.utils.log_decorator import log_decorator
import math

buyerView = Blueprint('buyerView', __name__)


def get_box_coordinates(lat, lon, distance):
    distance = distance * 1.609344
    lat = math.radians(lat)
    lon = math.radians(lon)

    radius = 6371
    parallel_radius = radius * math.cos(lat)

    lat_min = lat - distance / radius
    lat_max = lat + distance / radius
    lon_min = lon - distance / parallel_radius
    lon_max = lon + distance / parallel_radius

    lat_min = math.degrees(lat_min)
    lon_min = math.degrees(lon_min)
    lat_max = math.degrees(lat_max)
    lon_max = math.degrees(lon_max)

    return min(lat_min, lat_max), max(lat_min, lat_max), min(lon_min, lon_max), max(lon_min, lon_max)


def fetch_buyer_data_by_zip(params, cursor):
    query = f"""
                    select r.buyer_borrower1_name, count(*)
                    from glenn_working.public.relevant_base r
                    where r.zip_code = ?
                    and r.sale_amt between ? and ?
                    and r.sale_date between ? and ?
                    and r.bedrooms between ? and ?
                    and r.bathrooms between ? and ?
                    group by 1
                    order by 2 desc
                """

    cursor.execute(query, (
        params["zip"],
        params["salesPriceMin"],
        params["salesPriceMax"],
        params["saleDateMin"],
        params["saleDateMax"],
        params["bedsMin"],
        params["bedsMax"],
        params["bathsMin"],
        params["bathsMax"],
    ))


def fetch_buyer_data_by_coordinates(params, cursor):
    lat_min, lat_max, lon_min, lon_max = get_box_coordinates(
        params["coordinates"]["lat"],
        params["coordinates"]["lon"],
        int(params["searchRadius"]) or 0.1
    )

    query = f"""
        select r.buyer_borrower1_name, count(*)
        from glenn_working.public.relevant_base r
        where r.latitude >= ? and ? >= r.latitude
        and r.longitude >= ? and ? >= r.longitude
        and r.sale_amt between ? and ?
        and r.sale_date between ? and ?
        and r.bedrooms between ? and ?
        and r.bathrooms between ? and ?
        group by 1
        order by 2 desc
    """

    cursor.execute(query, (
        lat_min,
        lat_max,
        lon_min,
        lon_max,
        params["salesPriceMin"],
        params["salesPriceMax"],
        params["saleDateMin"],
        params["saleDateMax"],
        params["bedsMin"],
        params["bedsMax"],
        params["bathsMin"],
        params["bathsMax"],
    ))


@buyerView.route("/api/buyerView/getZipBuyerData", methods=["POST"])
@log_decorator
def getZipBuyerData():
    params = request.get_json()
    cursor = snowflake_conn.cursor()

    if "zip" in params:
        fetch_buyer_data_by_zip(params, cursor)
    else:
        fetch_buyer_data_by_coordinates(params, cursor)

    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


def fetch_buyer_detail_by_zip(params, cursor):
    query = f"""
                    select recording_date, buyer_borrower1_name, first_mtg_lender_name, buyer_borrower1_corp_ind, buyer_borrower1_ownership_rights_code, full_street_address, city, zip_code, sum_building_sqft, year_built, current_avm_value, sale_amt, sale_date, seller1_name, lender, latitude, longitude, corp_flag, disc_purchase, cash_buyer, private_lender
                    from glenn_working.public.relevant_base r
                    where r.zip_code = ?
                    and r.sale_amt between ? and ?
                    and r.sale_date between ? and ?
                    and r.bedrooms between ? and ?
                    and r.bathrooms between ? and ?
                """

    cursor.execute(query, (
        params["zip"],
        params["salesPriceMin"],
        params["salesPriceMax"],
        params["saleDateMin"],
        params["saleDateMax"],
        params["bedsMin"],
        params["bedsMax"],
        params["bathsMin"],
        params["bathsMax"],
    ))


def fetch_buyer_detail_by_coordinates(params, cursor):
    lat_min, lat_max, lon_min, lon_max = get_box_coordinates(
        params["coordinates"]["lat"],
        params["coordinates"]["lon"],
        int(params["searchRadius"]) or 0.1
    )

    query = f"""
                    select recording_date, buyer_borrower1_name, first_mtg_lender_name, buyer_borrower1_corp_ind, buyer_borrower1_ownership_rights_code, full_street_address, city, zip_code, sum_building_sqft, year_built, current_avm_value, sale_amt, sale_date, seller1_name, lender, latitude, longitude, corp_flag, disc_purchase, cash_buyer, private_lender
                    from glenn_working.public.relevant_base r
                    where r.latitude >= ? and ? >= r.latitude
                    and r.longitude >= ? and ? >= r.longitude
                    and r.sale_amt between ? and ?
                    and r.sale_date between ? and ?
                    and r.bedrooms between ? and ?
                    and r.bathrooms between ? and ?
                """

    cursor.execute(query, (
        lat_min,
        lat_max,
        lon_min,
        lon_max,
        params["salesPriceMin"],
        params["salesPriceMax"],
        params["saleDateMin"],
        params["saleDateMax"],
        params["bedsMin"],
        params["bedsMax"],
        params["bathsMin"],
        params["bathsMax"],
    ))


@buyerView.route("/api/buyerView/getZipBuyerDetail", methods=["POST"])
@log_decorator
def getZipBuyerDetail():
    params = request.get_json()
    cursor = snowflake_conn.cursor()

    if "zip" in params:
        fetch_buyer_detail_by_zip(params, cursor)
    else:
        fetch_buyer_detail_by_coordinates(params, cursor)

    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


@buyerView.route("/api/buyerView/getMarketBuyerData", methods=["POST"])
@log_decorator
def getMarketBuyerData():
    params = request.get_json()
    cursor = snowflake_conn.cursor()

    user = User.query.filter_by(id=g.uid).filter(User.billing_end_date >= datetime.now()).first()
    whereQuery = ''
    if (user):
        if (user.msas.find(params['selectedData']) == -1):
            whereQuery = f"""and r.recording_date < ?"""
    else:
        whereQuery = f"""and r.recording_date < ?"""

    if (params['selectedTab'] == "0"):
        query = f"""
                    select r.buyer_borrower1_name, count(*)
                    from relevant_base r
                    where r.city = ?
                    and r.recording_date between ? and ?
                    group by 1
                    order by 2 desc
                """
    else:
        query = f"""
                    select r.buyer_borrower1_name, count(*)
                    from relevant_base r
                    where r.msa = ?
                    and r.sale_date between ? and ?
                    {whereQuery}
                    group by 1
                    order by 2 desc
                """

    cursor.execute(query, (params['selectedData'],
    params['dateMin'],
    params['dateMax'],) if params['selectedTab'] == "0" else (
        params['selectedData'],
        params['dateMin'],
        params['dateMax'],
        str(datetime.now() - timedelta(days=365))
    ))
    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


@buyerView.route("/api/buyerView/getMarketTransactionList", methods=["POST"])
@log_decorator
def getMarketTransactionList():
    params = request.get_json()
    cursor = snowflake_conn.cursor()
    if (params['selectedTab'] == "0"):
        query = f"""
                    select recording_date, buyer_borrower1_name as buyer_name, first_mtg_amt as loan_amt, msa, full_street_address as address, city, zip_code, sum_building_sqft as sqft, year_built, current_avm_value as estimated_value, sale_date, seller1_name as seller_name, bedrooms, bathrooms, property_type, corp_flag as corporate_purchase, disc_purchase as discounted_purchase, cash_buyer, private_lender as private_lender_used, latitude, longitude
                    from relevant_base r
                    where r.city = ?
                    and r.recording_date between ? and ?
                """
    else:
        user = User.query.filter_by(id=g.uid).filter(User.billing_end_date >= datetime.now()).first()
        whereQuery = f"""and r.recording_date < ?"""
        addedColumn = ''

        if user and user.msas.find(params['selectedData']) != -1:
            additional_columns = ', phone, email'
            whereQuery = ''

        query = f"""
                    select recording_date, buyer_borrower1_name as buyer_name, first_mtg_amt as loan_amt, msa, full_street_address as address, city, zip_code, sum_building_sqft as sqft, year_built, current_avm_value as estimated_value, sale_date, seller1_name as seller_name, bedrooms, bathrooms, property_type, corp_flag as corporate_purchase, disc_purchase as discounted_purchase, cash_buyer, private_lender as private_lender_used, latitude, longitude {addedColumn}
                    from relevant_base r
                    where r.msa = ?
                    and r.sale_date between ? and ?
                    {whereQuery}
                """
    cursor.execute(query, (
        params['selectedData'],
        params["dateMin"],
        params["dateMax"]
    ) if params['selectedTab'] == "0" else (
        params['selectedData'],
        params["dateMin"],
        params["dateMax"],
        str(datetime.now() - timedelta(days=365))
    ))
    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


@buyerView.route("/api/buyerView/getMarketSelectBoxData", methods=["POST"])
@log_decorator
def getMarketSelectBoxData():
    params = request.get_json()
    cursor = snowflake_conn.cursor()
    if (params['selectedTab'] == "0"):
        query = f"""
                    select city from analytics.public.zip_mapping
                    {'where msa = ?' if params['msa'] else ''}
                    group by 1 order by 1 asc limit 100
                """
    else:
        query = f"""
                    select msa from analytics.public.zip_mapping group by 1 order by 1 asc
                """

    cursor.execute(query, (params["msa"]))
    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


@buyerView.route("/api/buyerView/getBuyers", methods=["POST"])
@log_decorator
def getBuyers():
    params = request.get_json()

    cursor = snowflake_conn.cursor()
    query = f"""
                select r.buyer_borrower1_name, count(*)
                from relevant_base r
                where r.msa ilike '%riverside%'
                {'and r.msa = ?' if params["msa"] else ''}
                group by 1
                order by 2 desc
                limit 100
            """

    cursor.execute(query, (params["msa"],))
    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


@buyerView.route("/api/buyerView/getBuyerTransactionList", methods=["POST"])
@log_decorator
def getBuyerTransactionList():
    params = request.get_json()
    cursor = snowflake_conn.cursor()
    query = f"""
                select recording_date, buyer_borrower1_name as buyer_name, first_mtg_amt as loan_amt, msa, full_street_address as address, city, zip_code, sum_building_sqft as sqft, year_built, current_avm_value as estimated_value, sale_date, seller1_name as seller_name, bedrooms, bathrooms, property_type, corp_flag as corporate_purchase, disc_purchase as discounted_purchase, cash_buyer, private_lender as private_lender_used, latitude, longitude
                from relevant_base r
                where buyer_borrower1_name = ?
                and r.msa ilike '%riverside%'
                {'and r.msa = ?' if params["msa"] else ''}
            """

    cursor.execute(query, (params["buyer"], params["msa"]))
    resData = cursor.fetchall()

    result = json.dumps([data for data in resData])

    return make_response(result, 200)


@buyerView.route("/api/buyerView/getAccessMsas", methods=["GET"])
@log_decorator
def getAccessMsas():
    user = User.query.filter_by(id=g.uid).filter(User.billing_end_date >= datetime.utcnow()).first()

    if (user):
        return make_response(jsonify(
            msas=user.msas,
            billing_start_date=user.billing_start_date,
            billing_end_date=user.billing_end_date,
        ), 200)
    else:
        return make_response(jsonify(
            msas='',
            billing_start_date='',
            billing_end_date='',
        ), 200)
