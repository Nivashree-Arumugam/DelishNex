-- ============================================================================
-- DelishNex – AI Powered Smart Restaurant Reservation & Food Ordering System
-- Database Schema for MySQL
-- ============================================================================
-- Run this script to create the database and all required tables.
-- Usage:  mysql -u root -p < database.sql
-- ============================================================================

-- Create the database if it does not exist
CREATE DATABASE IF NOT EXISTS delishnex
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE delishnex;

-- ============================================================================
-- TABLE: users
-- Stores all registered users (customers and admins).
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(120)  NOT NULL,
    email           VARCHAR(120)  NOT NULL,
    phone           VARCHAR(20)   NOT NULL,
    password_hash   VARCHAR(256)  NOT NULL,
    role            ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
    avatar_url      VARCHAR(256)  DEFAULT NULL,
    reward_points   INT           NOT NULL DEFAULT 0,
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: restaurants
-- Stores restaurant information.
-- ============================================================================
CREATE TABLE IF NOT EXISTS restaurants (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200)  NOT NULL,
    description     TEXT,
    address         VARCHAR(300)  NOT NULL,
    phone           VARCHAR(20),
    image_url       VARCHAR(256)  DEFAULT NULL,
    cuisine_type    VARCHAR(100),
    rating          DECIMAL(2,1)  NOT NULL DEFAULT 0.0,
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    opening_time    TIME          NOT NULL DEFAULT '09:00:00',
    closing_time    TIME          NOT NULL DEFAULT '23:00:00',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_restaurants_cuisine (cuisine_type),
    INDEX idx_restaurants_rating (rating)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: restaurant_tables
-- Stores individual tables inside each restaurant.
-- ============================================================================
CREATE TABLE IF NOT EXISTS restaurant_tables (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id   INT           NOT NULL,
    table_number    INT           NOT NULL,
    capacity        INT           NOT NULL DEFAULT 4,
    table_type      ENUM('regular', 'booth', 'outdoor', 'private', 'bar') NOT NULL DEFAULT 'regular',
    pos_x           INT           NOT NULL DEFAULT 0,
    pos_y           INT           NOT NULL DEFAULT 0,
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    UNIQUE INDEX idx_table_restaurant (restaurant_id, table_number)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: menu
-- Stores food / drink items offered by each restaurant.
-- ============================================================================
CREATE TABLE IF NOT EXISTS menu (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id   INT           NOT NULL,
    name            VARCHAR(200)  NOT NULL,
    description     TEXT,
    price           DECIMAL(10,2) NOT NULL,
    category        ENUM('starter', 'main_course', 'dessert', 'beverage', 'combo') NOT NULL,
    image_url       VARCHAR(256)  DEFAULT NULL,
    rating          DECIMAL(2,1)  NOT NULL DEFAULT 0.0,
    is_vegetarian   TINYINT(1)   NOT NULL DEFAULT 0,
    is_available    TINYINT(1)   NOT NULL DEFAULT 1,
    is_special      TINYINT(1)   NOT NULL DEFAULT 0,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    INDEX idx_menu_category (category),
    INDEX idx_menu_restaurant (restaurant_id),
    INDEX idx_menu_special (is_special)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: reservations
-- Stores table reservation requests from customers.
-- ============================================================================
CREATE TABLE IF NOT EXISTS reservations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT           NOT NULL,
    restaurant_id   INT           NOT NULL,
    table_id        INT           NOT NULL,
    occasion        VARCHAR(100),
    dining_mood     VARCHAR(100),
    reservation_date DATE         NOT NULL,
    reservation_time TIME         NOT NULL,
    members         INT           NOT NULL DEFAULT 2,
    status          ENUM('pending', 'confirmed', 'cancelled', 'completed') NOT NULL DEFAULT 'pending',
    special_request TEXT,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES restaurant_tables(id) ON DELETE CASCADE,
    INDEX idx_reservations_user (user_id),
    INDEX idx_reservations_date (reservation_date),
    INDEX idx_reservations_status (status)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: orders
-- Stores food orders placed by customers.
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT           NOT NULL,
    restaurant_id   INT           NOT NULL,
    reservation_id  INT           DEFAULT NULL,
    subtotal        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    gst             DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    service_charge  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    grand_total     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    coupon_code     VARCHAR(50)   DEFAULT NULL,
    status          ENUM('pending', 'preparing', 'ready', 'delivered', 'cancelled') NOT NULL DEFAULT 'pending',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL,
    INDEX idx_orders_user (user_id),
    INDEX idx_orders_status (status)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: order_items
-- Stores individual items within an order.
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    order_id        INT           NOT NULL,
    menu_id         INT           NOT NULL,
    quantity        INT           NOT NULL DEFAULT 1,
    unit_price      DECIMAL(10,2) NOT NULL,
    total_price     DECIMAL(10,2) NOT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_id) REFERENCES menu(id) ON DELETE CASCADE,
    INDEX idx_order_items_order (order_id)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: payments
-- Stores payment records for orders.
-- ============================================================================
CREATE TABLE IF NOT EXISTS payments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    order_id        INT           NOT NULL,
    user_id         INT           NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    payment_method  ENUM('upi', 'card', 'wallet', 'cash') NOT NULL DEFAULT 'cash',
    payment_status  ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    transaction_id  VARCHAR(100)  DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_payments_order (order_id),
    INDEX idx_payments_status (payment_status)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: rewards
-- Stores reward point transactions for users.
-- ============================================================================
CREATE TABLE IF NOT EXISTS rewards (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT           NOT NULL,
    points          INT           NOT NULL,
    description     VARCHAR(256)  NOT NULL,
    reward_type     ENUM('earned', 'redeemed') NOT NULL DEFAULT 'earned',
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_rewards_user (user_id)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: reviews
-- Stores customer reviews for restaurants and menu items.
-- ============================================================================
CREATE TABLE IF NOT EXISTS reviews (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT           NOT NULL,
    restaurant_id   INT           NOT NULL,
    order_id        INT           DEFAULT NULL,
    rating          DECIMAL(2,1)  NOT NULL,
    comment         TEXT,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    INDEX idx_reviews_restaurant (restaurant_id)
) ENGINE=InnoDB;


-- ============================================================================
-- SEED DATA
-- ============================================================================

-- ── Admin User (password: admin123) ────────────────────────────────────
INSERT INTO users (full_name, email, phone, password_hash, role, reward_points)
VALUES (
    'Admin User',
    'admin@delishnex.com',
    '9999999999',
    'scrypt:32768:8:1$salt$adminhashedpasswordplaceholder',
    'admin',
    0
);

-- ── Sample Restaurants ─────────────────────────────────────────────────
INSERT INTO restaurants (name, description, address, phone, cuisine_type, rating, opening_time, closing_time) VALUES
('The Green Terrace', 'A beautiful rooftop restaurant with a stunning city view, offering a blend of contemporary Indian and Continental cuisine.', '42 MG Road, Bengaluru', '9876543210', 'Multi-Cuisine', 4.5, '11:00:00', '23:00:00'),
('Spice Garden', 'An authentic South Indian experience with traditional recipes passed down through generations.', '15 Anna Salai, Chennai', '9876543211', 'South Indian', 4.3, '08:00:00', '22:00:00'),
('The Royal Plate', 'Fine dining with a royal touch. Experience Mughlai and North Indian delicacies in an opulent setting.', '7 Connaught Place, New Delhi', '9876543212', 'North Indian', 4.7, '12:00:00', '23:30:00'),
('Ocean Breeze', 'Fresh seafood and coastal flavors with a panoramic sea view.', '23 Marine Drive, Mumbai', '9876543213', 'Seafood', 4.4, '11:00:00', '23:00:00'),
('Bamboo Kitchen', 'Pan-Asian cuisine featuring the best of Chinese, Thai, and Japanese cooking.', '8 Park Street, Kolkata', '9876543214', 'Pan-Asian', 4.2, '11:30:00', '22:30:00'),
('La Dolce Vita', 'Authentic Italian cuisine with hand-tossed pizzas, fresh pasta, and artisan desserts.', '31 Brigade Road, Bengaluru', '9876543215', 'Italian', 4.6, '12:00:00', '23:00:00');

-- ── Tables for The Green Terrace (restaurant_id=1) ─────────────────────
INSERT INTO restaurant_tables (restaurant_id, table_number, capacity, table_type, pos_x, pos_y) VALUES
(1, 1, 2, 'regular', 1, 1), (1, 2, 2, 'regular', 2, 1), (1, 3, 4, 'regular', 3, 1),
(1, 4, 4, 'booth', 1, 2),   (1, 5, 4, 'booth', 2, 2),   (1, 6, 6, 'regular', 3, 2),
(1, 7, 2, 'outdoor', 1, 3), (1, 8, 4, 'outdoor', 2, 3), (1, 9, 8, 'private', 3, 3),
(1, 10, 2, 'bar', 1, 4),    (1, 11, 2, 'bar', 2, 4),    (1, 12, 4, 'regular', 3, 4);

-- ── Tables for Spice Garden (restaurant_id=2) ──────────────────────────
INSERT INTO restaurant_tables (restaurant_id, table_number, capacity, table_type, pos_x, pos_y) VALUES
(2, 1, 2, 'regular', 1, 1), (2, 2, 4, 'regular', 2, 1), (2, 3, 4, 'booth', 3, 1),
(2, 4, 6, 'regular', 1, 2), (2, 5, 2, 'outdoor', 2, 2), (2, 6, 4, 'outdoor', 3, 2),
(2, 7, 8, 'private', 1, 3), (2, 8, 2, 'bar', 2, 3),     (2, 9, 4, 'regular', 3, 3),
(2, 10, 2, 'regular', 1, 4);

-- ── Tables for The Royal Plate (restaurant_id=3) ───────────────────────
INSERT INTO restaurant_tables (restaurant_id, table_number, capacity, table_type, pos_x, pos_y) VALUES
(3, 1, 2, 'regular', 1, 1), (3, 2, 4, 'booth', 2, 1), (3, 3, 4, 'regular', 3, 1),
(3, 4, 6, 'private', 1, 2), (3, 5, 2, 'regular', 2, 2), (3, 6, 4, 'outdoor', 3, 2),
(3, 7, 8, 'private', 1, 3), (3, 8, 2, 'bar', 2, 3),     (3, 9, 4, 'regular', 3, 3),
(3, 10, 4, 'booth', 1, 4), (3, 11, 2, 'regular', 2, 4), (3, 12, 6, 'regular', 3, 4);

-- ── Tables for Ocean Breeze (restaurant_id=4) ──────────────────────────
INSERT INTO restaurant_tables (restaurant_id, table_number, capacity, table_type, pos_x, pos_y) VALUES
(4, 1, 2, 'outdoor', 1, 1), (4, 2, 4, 'outdoor', 2, 1), (4, 3, 4, 'regular', 3, 1),
(4, 4, 6, 'regular', 1, 2), (4, 5, 2, 'bar', 2, 2),     (4, 6, 4, 'booth', 3, 2),
(4, 7, 8, 'private', 1, 3), (4, 8, 2, 'regular', 2, 3), (4, 9, 4, 'regular', 3, 3),
(4, 10, 2, 'outdoor', 1, 4);

-- ── Tables for Bamboo Kitchen (restaurant_id=5) ────────────────────────
INSERT INTO restaurant_tables (restaurant_id, table_number, capacity, table_type, pos_x, pos_y) VALUES
(5, 1, 2, 'regular', 1, 1), (5, 2, 4, 'regular', 2, 1), (5, 3, 4, 'booth', 3, 1),
(5, 4, 6, 'regular', 1, 2), (5, 5, 2, 'bar', 2, 2),     (5, 6, 4, 'regular', 3, 2),
(5, 7, 8, 'private', 1, 3), (5, 8, 2, 'regular', 2, 3);

-- ── Tables for La Dolce Vita (restaurant_id=6) ─────────────────────────
INSERT INTO restaurant_tables (restaurant_id, table_number, capacity, table_type, pos_x, pos_y) VALUES
(6, 1, 2, 'regular', 1, 1), (6, 2, 2, 'regular', 2, 1), (6, 3, 4, 'booth', 3, 1),
(6, 4, 4, 'regular', 1, 2), (6, 5, 6, 'regular', 2, 2), (6, 6, 4, 'outdoor', 3, 2),
(6, 7, 8, 'private', 1, 3), (6, 8, 2, 'bar', 2, 3),     (6, 9, 4, 'regular', 3, 3),
(6, 10, 2, 'outdoor', 1, 4), (6, 11, 4, 'booth', 2, 4), (6, 12, 6, 'private', 3, 4);

-- ── Menu Items for The Green Terrace (restaurant_id=1) ─────────────────
INSERT INTO menu (restaurant_id, name, description, price, category, rating, is_vegetarian, is_available, is_special) VALUES
(1, 'Paneer Tikka', 'Marinated cottage cheese cubes grilled to perfection in a tandoor.', 299.00, 'starter', 4.5, 1, 1, 1),
(1, 'Chicken Seekh Kebab', 'Minced chicken kebabs with aromatic spices, served with mint chutney.', 349.00, 'starter', 4.6, 0, 1, 0),
(1, 'Crispy Corn', 'Golden fried corn kernels tossed with spicy seasoning.', 249.00, 'starter', 4.3, 1, 1, 0),
(1, 'Mushroom Galawat', 'Melt-in-mouth mushroom patties with a secret blend of spices.', 279.00, 'starter', 4.4, 1, 1, 0),
(1, 'Butter Chicken', 'Tender chicken in a rich, creamy tomato-based gravy. A timeless classic.', 399.00, 'main_course', 4.8, 0, 1, 1),
(1, 'Dal Makhani', 'Slow-cooked black lentils in a buttery, creamy sauce.', 299.00, 'main_course', 4.5, 1, 1, 0),
(1, 'Mutton Biryani', 'Fragrant basmati rice layered with tender mutton and aromatic spices.', 449.00, 'main_course', 4.7, 0, 1, 1),
(1, 'Paneer Butter Masala', 'Cottage cheese cubes in a luscious butter tomato gravy.', 329.00, 'main_course', 4.4, 1, 1, 0),
(1, 'Veg Fried Rice', 'Wok-tossed rice with fresh vegetables and soy sauce.', 249.00, 'main_course', 4.2, 1, 1, 0),
(1, 'Gulab Jamun', 'Soft, spongy milk-solid dumplings soaked in rose-flavored sugar syrup.', 149.00, 'dessert', 4.6, 1, 1, 1),
(1, 'Chocolate Lava Cake', 'A warm chocolate cake with a molten center, served with vanilla ice cream.', 249.00, 'dessert', 4.8, 1, 1, 0),
(1, 'Rasmalai', 'Soft paneer discs in sweetened, flavored milk.', 179.00, 'dessert', 4.5, 1, 1, 0),
(1, 'Mango Lassi', 'Creamy yogurt blended with fresh mango pulp.', 129.00, 'beverage', 4.4, 1, 1, 0),
(1, 'Masala Chai', 'Traditional Indian spiced tea brewed to perfection.', 79.00, 'beverage', 4.3, 1, 1, 0),
(1, 'Fresh Lime Soda', 'Refreshing lime juice with soda, sweet or salted.', 99.00, 'beverage', 4.2, 1, 1, 0),
(1, 'Royal Feast Combo', 'Butter Chicken + Dal Makhani + 2 Naan + Gulab Jamun + Mango Lassi.', 749.00, 'combo', 4.7, 0, 1, 1),
(1, 'Veg Delight Combo', 'Paneer Tikka + Paneer Butter Masala + 2 Roti + Rasmalai + Masala Chai.', 649.00, 'combo', 4.5, 1, 1, 0);

-- ── Menu Items for Spice Garden (restaurant_id=2) ──────────────────────
INSERT INTO menu (restaurant_id, name, description, price, category, rating, is_vegetarian, is_available, is_special) VALUES
(2, 'Medu Vada', 'Crispy lentil donuts served with coconut chutney and sambar.', 129.00, 'starter', 4.3, 1, 1, 0),
(2, 'Chicken 65', 'Deep-fried spicy chicken bites, a South Indian classic.', 299.00, 'starter', 4.5, 0, 1, 1),
(2, 'Masala Dosa', 'Crispy rice crepe filled with spiced potato filling, served with chutneys.', 179.00, 'main_course', 4.7, 1, 1, 1),
(2, 'Chettinad Chicken', 'Fiery chicken curry from the Chettinad region with freshly ground spices.', 379.00, 'main_course', 4.6, 0, 1, 1),
(2, 'Sambar Rice', 'Steamed rice served with aromatic lentil stew and vegetables.', 199.00, 'main_course', 4.4, 1, 1, 0),
(2, 'Payasam', 'Traditional South Indian dessert made with milk, vermicelli, and nuts.', 129.00, 'dessert', 4.5, 1, 1, 0),
(2, 'Filter Coffee', 'Authentic South Indian filter coffee, strong and aromatic.', 69.00, 'beverage', 4.8, 1, 1, 1),
(2, 'Spice Garden Thali', 'Masala Dosa + Sambar Rice + Medu Vada + Payasam + Filter Coffee.', 449.00, 'combo', 4.6, 1, 1, 1);

-- ── Menu Items for The Royal Plate (restaurant_id=3) ───────────────────
INSERT INTO menu (restaurant_id, name, description, price, category, rating, is_vegetarian, is_available, is_special) VALUES
(3, 'Galouti Kebab', 'Ultra-tender minced lamb kebabs with a royal blend of 150 spices.', 449.00, 'starter', 4.8, 0, 1, 1),
(3, 'Dahi Ke Kebab', 'Creamy hung-curd kebabs, crispy outside and soft inside.', 299.00, 'starter', 4.4, 1, 1, 0),
(3, 'Mughlai Chicken Curry', 'Rich, aromatic chicken curry with cashew and saffron.', 449.00, 'main_course', 4.7, 0, 1, 1),
(3, 'Dum Biryani', 'Slow-cooked layered biryani with aromatic rice and tender meat.', 499.00, 'main_course', 4.9, 0, 1, 1),
(3, 'Shahi Paneer', 'Paneer in a rich, creamy gravy with nuts and saffron.', 349.00, 'main_course', 4.5, 1, 1, 0),
(3, 'Phirni', 'Chilled rice pudding with saffron, cardamom, and pistachios.', 199.00, 'dessert', 4.6, 1, 1, 0),
(3, 'Thandai', 'Refreshing spiced milk drink with nuts and saffron.', 149.00, 'beverage', 4.5, 1, 1, 0),
(3, 'Royal Feast', 'Galouti Kebab + Dum Biryani + Shahi Paneer + Phirni + Thandai.', 999.00, 'combo', 4.8, 0, 1, 1);

-- ── Menu Items for Ocean Breeze (restaurant_id=4) ──────────────────────
INSERT INTO menu (restaurant_id, name, description, price, category, rating, is_vegetarian, is_available, is_special) VALUES
(4, 'Prawn Tempura', 'Lightly battered and fried prawns served with a tangy dip.', 399.00, 'starter', 4.5, 0, 1, 1),
(4, 'Fish Tikka', 'Marinated fish fillets grilled in a tandoor with coastal spices.', 349.00, 'starter', 4.4, 0, 1, 0),
(4, 'Goan Fish Curry', 'Traditional Goan fish curry with coconut and tamarind.', 429.00, 'main_course', 4.7, 0, 1, 1),
(4, 'Lobster Thermidor', 'Creamy lobster baked with cheese and herbs. A premium delicacy.', 1299.00, 'main_course', 4.9, 0, 1, 1),
(4, 'Coconut Rice', 'Fragrant rice cooked with fresh coconut and curry leaves.', 199.00, 'main_course', 4.3, 1, 1, 0),
(4, 'Coconut Panna Cotta', 'Silky coconut cream dessert with tropical fruit compote.', 249.00, 'dessert', 4.6, 1, 1, 0),
(4, 'Blue Lagoon Mocktail', 'Refreshing blue curacao and lemonade mocktail.', 179.00, 'beverage', 4.4, 1, 1, 0),
(4, 'Seafood Platter', 'Prawn Tempura + Goan Fish Curry + Coconut Rice + Coconut Panna Cotta.', 899.00, 'combo', 4.7, 0, 1, 1);

-- ── Menu Items for Bamboo Kitchen (restaurant_id=5) ────────────────────
INSERT INTO menu (restaurant_id, name, description, price, category, rating, is_vegetarian, is_available, is_special) VALUES
(5, 'Dim Sum Platter', 'Assorted steamed dumplings with pork and vegetable fillings.', 349.00, 'starter', 4.5, 0, 1, 1),
(5, 'Thai Spring Rolls', 'Crispy rolls filled with glass noodles, vegetables, and Thai herbs.', 249.00, 'starter', 4.3, 1, 1, 0),
(5, 'Kung Pao Chicken', 'Stir-fried chicken with peanuts, chillies, and Sichuan pepper.', 379.00, 'main_course', 4.6, 0, 1, 1),
(5, 'Pad Thai', 'Classic Thai stir-fried rice noodles with tofu, peanuts, and bean sprouts.', 329.00, 'main_course', 4.5, 1, 1, 1),
(5, 'Sushi Roll Set', 'Assorted sushi rolls with salmon, tuna, and avocado.', 599.00, 'main_course', 4.7, 0, 1, 0),
(5, 'Mochi Ice Cream', 'Japanese rice cake filled with creamy ice cream in assorted flavors.', 199.00, 'dessert', 4.4, 1, 1, 0),
(5, 'Thai Iced Tea', 'Creamy, sweet Thai tea served over ice.', 129.00, 'beverage', 4.3, 1, 1, 0),
(5, 'Asian Explorer Combo', 'Dim Sum + Kung Pao Chicken + Pad Thai + Mochi Ice Cream + Thai Iced Tea.', 799.00, 'combo', 4.6, 0, 1, 1);

-- ── Menu Items for La Dolce Vita (restaurant_id=6) ─────────────────────
INSERT INTO menu (restaurant_id, name, description, price, category, rating, is_vegetarian, is_available, is_special) VALUES
(6, 'Bruschetta', 'Toasted bread topped with fresh tomatoes, basil, and olive oil.', 249.00, 'starter', 4.4, 1, 1, 0),
(6, 'Caprese Salad', 'Fresh mozzarella, tomatoes, and basil drizzled with balsamic glaze.', 299.00, 'starter', 4.5, 1, 1, 1),
(6, 'Margherita Pizza', 'Classic wood-fired pizza with San Marzano tomatoes and fresh mozzarella.', 399.00, 'main_course', 4.7, 1, 1, 1),
(6, 'Pasta Carbonara', 'Creamy pasta with pancetta, egg yolk, and Parmesan cheese.', 449.00, 'main_course', 4.6, 0, 1, 1),
(6, 'Risotto Funghi', 'Creamy Arborio rice with wild mushrooms and truffle oil.', 429.00, 'main_course', 4.5, 1, 1, 0),
(6, 'Tiramisu', 'Classic Italian dessert with layers of coffee-soaked ladyfingers and mascarpone.', 279.00, 'dessert', 4.8, 1, 1, 1),
(6, 'Panna Cotta', 'Silky vanilla cream dessert with berry coulis.', 249.00, 'dessert', 4.6, 1, 1, 0),
(6, 'Espresso', 'Strong, rich Italian espresso made with premium Arabica beans.', 129.00, 'beverage', 4.5, 1, 1, 0),
(6, 'Limoncello Spritz', 'Refreshing Italian lemon spritz mocktail.', 179.00, 'beverage', 4.4, 1, 1, 0),
(6, 'Italian Feast Combo', 'Bruschetta + Margherita Pizza + Pasta Carbonara + Tiramisu + Espresso.', 999.00, 'combo', 4.7, 0, 1, 1);
