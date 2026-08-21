-- PostgreSQL Schema for PUC Digital Bookstore
CREATE DATABASE puc_bookstore;
-- 1. USER Table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'Customer' CHECK (role IN ('Customer', 'Staff', 'Admin')),
    employee_id VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. BOOK Table
CREATE TABLE IF NOT EXISTS books (
    book_id SERIAL PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    cover_img VARCHAR(500)
);

-- 3. DEPARTMENT Table
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- 4. BOOK_DEPARTMENT Bridge
CREATE TABLE IF NOT EXISTS book_departments (
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    department_id INT NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, department_id)
);

-- 5. ORDER Table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id), -- Customer
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Ready for Pickup', 'Picked Up', 'Cancelled')),
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50),
    stripe_payment_id VARCHAR(255),
    pickup_pin VARCHAR(10) NOT NULL,
    prepared_location VARCHAR(255),
    prepared_by_staff_id INT DEFAULT NULL REFERENCES users(user_id),
    released_by_staff_id INT DEFAULT NULL REFERENCES users(user_id),
    picked_up_at TIMESTAMP
);

-- 6. ORDER_ITEM Table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    book_id INT NOT NULL REFERENCES books(book_id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- 7. CART_ITEM Table
CREATE TABLE IF NOT EXISTS cart_items (
    cart_item_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    book_id INT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initial Departments
INSERT INTO departments (name) VALUES
('Computer Science'),
('Business'),
('Law'),
('Arts & Humanities')
ON CONFLICT (name) DO NOTHING;
