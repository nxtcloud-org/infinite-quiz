-- 데이터베이스 생성 (이미 존재할 경우 생략 가능)
-- CREATE DATABASE IF NOT EXISTS my_database;
-- USE my_database;

-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    password TEXT NOT NULL,
    school TEXT,
    team TEXT,
    points INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    incorrect INTEGER DEFAULT 0
);

-- 문제풀이 결과 테이블 생성 (한국 서울 시간대 기준으로 기록)
CREATE TABLE IF NOT EXISTS question_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_idx INTEGER NOT NULL,
    topic TEXT,
    user_id INTEGER NOT NULL,
    correct BOOLEAN,
    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

