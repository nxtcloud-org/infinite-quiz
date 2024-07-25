import streamlit as st
import sqlite3
import pandas as pd
import config

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('db/db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# 테이블 목록 가져오기
def get_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]

# 테이블 데이터 가져오기
def get_table_data(table_name):
    conn = get_db_connection()
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 데이터 수정하기
def update_data(table_name, id_column, id_value, column, new_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"UPDATE {table_name} SET {column} = ? WHERE {id_column} = ?"
    cursor.execute(query, (new_value, id_value))
    conn.commit()
    conn.close()

# 데이터 삭제하기
def delete_data(table_name, id_column, id_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
    cursor.execute(query, (id_value,))
    conn.commit()
    conn.close()

# 메인 앱
def main():
    st.set_page_config(page_title="관리자 대시보드", page_icon="🔒", layout="wide")
    st.title("🔒 관리자 대시보드")

    # 세션 상태 초기화
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False

    # 관리자 인증
    if not st.session_state.admin_authenticated:
        admin_password = st.text_input("관리자 비밀번호를 입력하세요", type="password")
        if st.button("로그인"):
            if admin_password == config.ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("인증 성공!")
                st.rerun()
            else:
                st.error("잘못된 비밀번호입니다.")
        return

    # 관리자 인증 후 대시보드 표시
    tables = get_tables()
    selected_table = st.selectbox("테이블 선택", tables)

    if selected_table:
        df = get_table_data(selected_table)
        st.subheader(f"{selected_table} 테이블 데이터")
        st.dataframe(df)

        # 데이터 수정
        st.subheader("데이터 수정")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            id_column = st.selectbox("ID 열 선택", df.columns)
        with col2:
            id_value = st.selectbox("ID 값 선택", df[id_column].unique())
        with col3:
            column_to_update = st.selectbox("수정할 열 선택", df.columns)
        with col4:
            new_value = st.text_input("새 값 입력")
        if st.button("수정"):
            update_data(selected_table, id_column, id_value, column_to_update, new_value)
            st.success("데이터가 수정되었습니다.")
            st.rerun()

        # 데이터 삭제
        st.subheader("데이터 삭제")
        col1, col2 = st.columns(2)
        with col1:
            delete_id_column = st.selectbox("삭제할 행의 ID 열 선택", df.columns, key="delete_id_column")
        with col2:
            delete_id_value = st.selectbox("삭제할 행의 ID 값 선택", df[delete_id_column].unique(), key="delete_id_value")
        if st.button("삭제", type="primary"):
            delete_data(selected_table, delete_id_column, delete_id_value)
            st.success("데이터가 삭제되었습니다.")
            st.rerun()

    # 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        st.session_state.admin_authenticated = False
        st.rerun()

if __name__ == "__main__":
    main()