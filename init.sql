
DROP TABLE IF EXISTS article_votes;
DROP TABLE IF EXISTS user_authority;
DROP TABLE IF EXISTS authority_requests;
DROP TABLE IF EXISTS arxiv_article_subcategories;
DROP TABLE IF EXISTS arxiv_article_authors;
DROP TABLE IF EXISTS arxiv_articles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS article_score_aggregates;
DROP TABLE IF EXISTS request_timestamps;

-- CREATE DATABASE IF NOT EXISTS rate_my_arxiv;

USE rate_my_arxiv;

-- Users table to manage user authentication and verification
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score_multiplier FLOAT DEFAULT 0.5
);

-- Arxiv articles table with authors and categories as comma-separated fields
CREATE TABLE IF NOT EXISTS arxiv_articles (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    authors TEXT NOT NULL,  -- Storing authors as a comma-separated list
    categories TEXT,  -- Storing categories as a comma-separated list
    published timestamp,
    pdf_url TEXT,
    arxiv_url TEXT
);

-- Article voting table, which holds user scores for different articles
CREATE TABLE IF NOT EXISTS article_votes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    article_id VARCHAR(255) NOT NULL,
    authority_score FLOAT NOT NULL,
    truthworthiness_score FLOAT NOT NULL,
    sentiment_score FLOAT NOT NULL,
    conciseness_score FLOAT NOT NULL,
    readability_score FLOAT NOT NULL,
    transparency_score FLOAT NOT NULL,
    weight_multiplier FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES arxiv_articles(id) ON DELETE CASCADE
);

-- Materialized view to aggregate scores for each article based on user votes
CREATE TABLE IF NOT EXISTS article_score_aggregates (
    article_id VARCHAR(255) PRIMARY KEY,
    authority_score FLOAT DEFAULT 0,
    truthworthiness_score FLOAT DEFAULT 0,
    sentiment_score FLOAT DEFAULT 0,
    conciseness_score FLOAT DEFAULT 0,
    readability_score FLOAT DEFAULT 0,
    transparency_score FLOAT DEFAULT 0
);

CREATE TABLE request_timestamps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    last_request TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE authority_requests (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    details TEXT NOT NULL,
    resume MEDIUMBLOB ,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Security 
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost');

REVOKE DROP, TRUNCATE ON *.* FROM 'application'@'%';
REVOKE DROP, TRUNCATE ON `rate_my_arxiv`.* FROM 'application'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON `rate_my_arxiv`.* TO 'application'@'%';

DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test_%';
DELETE FROM mysql.user WHERE User='';

FLUSH PRIVILEGES;