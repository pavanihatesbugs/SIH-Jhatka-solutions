import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)

def get_pan_record(pan_num):

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT  name, fathers_name, dob
        FROM pan
        WHERE pan_num = %s
        """,
        (pan_num,)
    )

    row = cursor.fetchone()

    cursor.close()

    if row is None:
        return None

    return {
       
        "name": row[0],
        "fathers_name": row[1],
        "dob": str(row[2])
    }

def get_aadhaar_record(aadhaar_id):

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT  name, dob, gender, vid
        FROM aadhaar
        WHERE aadhaar_id = %s
        """,
        (aadhaar_id,)
    )

    row = cursor.fetchone()

    cursor.close()

    if row is None:
        return None

    return {
        
        "name": row[0],
        "dob": str(row[1]),
        "gender": row[2],
        "vid": row[3]
    }

def get_passport_record(passport_num):

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ptype,country_code,surname, name,nationality,gender,dob,pob,placeOfIssue,dateOfIssue,dateOfExpiry
        FROM passport
        WHERE passport_num = %s
        """,
        (passport_num,)
    )

    row = cursor.fetchone()

    cursor.close()

    if row is None:
        return None

    return {
        "ptype": row[0],
        "country_code": row[1],
        "surname": str(row[2]),
        "name": row[3],
        "nationality": row[4],
        "gender":row[5],
        "dob":row[6],
        "pob":row[7],
        "placeOfIssue":row[8],
        "dateOfIssue":row[9],
        "dateOfExpiry":row[10]
    }