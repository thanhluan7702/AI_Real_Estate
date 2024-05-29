import os 
from dotenv import load_dotenv

import psycopg2

load_dotenv('.env')

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT')
DB_HOST = os.getenv('DB_HOST')

def _connect(): 
    try: 
        conn = psycopg2.connect(
                    database = DB_NAME,
                    user = DB_USERNAME,
                    password = DB_PASSWORD, 
                    host = DB_HOST,
                    port = DB_PORT
                    )
        cursor = conn.cursor()
        print("======== Connect to the database ========")
        
        return conn, cursor
    
    except psycopg2.ConnectionError as e: 
        print(f">>> Error connecting to database\n{e}")
        
        
def _close(connection, cursor):
    if connection: 
        connection.close()
        print("======== Connection closed ========")
        
    if cursor: 
        cursor.close()
        print("======== Cursor closed ========")


def create_alonhadat_table(conn, cursor): 
    query = '''
        CREATE TABLE IF NOT EXISTS ALONHADAT(
            "ID" SERIAL PRIMARY KEY,
            "post_id" INT, 
            "Loại tin" TEXT, 
            "Tiêu đề" TEXT, 
            "Mô tả" TEXT, 
            "Giá" TEXT, 
            "Diện tích" TEXT, 
            "Địa chỉ" TEXT, 
            "Mã tin" TEXT,
            "Hướng" TEXT,
            "Phòng ăn" TEXT,
            "Đường trước nhà" TEXT,
            "Nhà bếp" TEXT,
            "Loại BDS" TEXT,
            "Pháp lý" TEXT,
            "Sân thượng" TEXT,
            "Chiều ngang" TEXT,
            "Số lầu" TEXT,
            "Chổ để xe hơi" TEXT,
            "Chiều dài" TEXT,
            "Số phòng ngủ" TEXT,
            "Chính chủ" TEXT,
            "URL" TEXT,
            "date" TEXT,
            "Liên hệ" TEXT,
            "phone" TEXT,
            "Thuộc dự án" TEXT
        )
    '''
    cursor.execute(query)
    conn.commit()
    print("======== TABLE CREATED SUCCESSFULLY ========")
    return 

def create_nhatot_table(conn, cursor): 
    query = '''
        CREATE TABLE IF NOT EXISTS NHATOT ( 
            "ID" SERIAL PRIMARY KEY,
            "post_id" INT,  
            "Loại tin" TEXT,
            "Tiêu đề" TEXT,
            "Giá" TEXT,
            "Diện tích" TEXT,
            "Địa chỉ" TEXT,
            "Giá/m2" TEXT,
            "Giấy tờ pháp lý" TEXT,
            "Loại hình đất" TEXT,
            "Mô tả" TEXT,
            "URL" TEXT,
            "date" TEXT,
            "Đặc điểm nhà/đất" TEXT,
            "Số phòng ngủ" TEXT,
            "Số phòng vệ sinh" TEXT,
            "Loại hình nhà ở" TEXT,
            "Diện tích sử dụng" TEXT,
            "Tổng số tầng" TEXT,
            "Tình trạng nội thất" TEXT,
            "Tên phân khu/Lô/Block/Tháp" TEXT,
            "Tình trạng bất động sản" TEXT,
            "Tầng số" TEXT,
            "Hướng ban công" TEXT,
            "Loại hình căn hộ" TEXT,
            "Loại hình văn phòng" TEXT,
            "Mã căn" TEXT,
            "Đặc điểm căn hộ" TEXT,
            "Mã lô" TEXT,
            "Số tiền cọc" TEXT,
            "Diện tích đất" TEXT,
            "Liên hệ" TEXT, 
            "card_visit" TEXT
        )
    '''
    cursor.execute(query)
    conn.commit() 
    print("======== TABLE CREATED SUCCESSFULLY ========")
    return

def create_batdongsan_table(conn, cursor): 
    query = '''
        CREATE TABLE IF NOT EXISTS BATDONGSAN ( 
          "ID" SERIAL PRIMARY KEY,
          "post_id" INT,  
          "Loại tin" TEXT,
          "Tiêu đề" TEXT,
          "Địa chỉ" TEXT,
          "Mô tả" TEXT,
          "Diện tích" TEXT,
          "Mức giá" TEXT,
          "Mặt tiền" TEXT,
          "Đường vào" TEXT,
          "Hướng nhà" TEXT,
          "Hướng ban công" TEXT,
          "Số tầng" TEXT, 
          "Số phòng ngủ" TEXT,
          "Số toilet" TEXT,
          "URL" TEXT,
          "date" TEXT,
          "Liên hệ" TEXT,
          "card_visit" TEXT,
          "Pháp lý" TEXT,
          "Nội thất" TEXT   
        )
    '''
    cursor.execute(query)
    conn.commit()
    print("======== TABLE CREATED SUCCESSFULLY ========")
    return

def insert_df(conn, cursor, table_name, lst_record):
    error = []
    
    def insert_data(record):
        # insert data function for single record
        columns = ', '.join('"' + col + '"' for col in record.keys())
        values = record.values()
        placeholder = ', '.join(['%s'] * len(values))

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholder})"
        try:
            cursor.execute(query, tuple(values))
        except Exception as e:
            print(e)
            error.append(record)
            conn.rollback()  # Rollback the transaction if an error occurs
        else:
            conn.commit()  # Commit the transaction if no error occurs
        
    # insert list of records to database
    for record in lst_record:
        insert_data(record)
        
    return None, error