-- ============================================================
-- Event Bridge — MySQL schema (matches event_bridge_app.py models)
-- Engine: InnoDB | Charset: utf8mb4
-- Tables created in FK-dependency order.
--
-- This script is optional: the application calls db.create_all() on
-- startup and creates these tables automatically. Use this file for
-- manual/explicit initialization (e.g. Railway MySQL "Data" tab) or
-- as documentation of the expected schema. All statements use
-- IF NOT EXISTS so it is safe to run alongside db.create_all().
-- ============================================================
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) NOT NULL,
    phone       VARCHAR(50)  NULL,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(20)  NOT NULL,
    dept        VARCHAR(150) NULL,
    reg_no      VARCHAR(50)  NULL,
    is_blocked  TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_users_email (email),
    KEY idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. active_sessions
CREATE TABLE IF NOT EXISTS active_sessions (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    email     VARCHAR(255) NOT NULL,
    login_at  DATETIME     NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_active_sessions_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. events
CREATE TABLE IF NOT EXISTS events (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    organizer_id  INT           NOT NULL,
    name          VARCHAR(255)  NOT NULL,
    description   TEXT          NULL,
    venue         VARCHAR(255)  NOT NULL,
    category      VARCHAR(100)  NOT NULL,
    event_date    DATETIME      NOT NULL,
    team_size     INT           NULL DEFAULT 1,
    entry_fee     DECIMAL(10,2) NULL DEFAULT 0.00,
    total_seats   INT           NOT NULL,
    status        VARCHAR(20)   NULL DEFAULT 'Upcoming',
    created_at    DATETIME      NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_events_organizer (organizer_id),
    KEY idx_events_category (category),
    CONSTRAINT fk_events_organizer FOREIGN KEY (organizer_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. registrations
CREATE TABLE IF NOT EXISTS registrations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    event_id        INT          NOT NULL,
    user_id         INT          NOT NULL,
    team_name       VARCHAR(150) NULL,
    status          VARCHAR(20)  NULL DEFAULT 'Pending',
    payment_status  VARCHAR(20)  NULL DEFAULT 'Pending',
    attended        TINYINT(1)   NOT NULL DEFAULT 0,
    registered_at   DATETIME     NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_reg_event (event_id),
    KEY idx_reg_user (user_id),
    CONSTRAINT fk_reg_event FOREIGN KEY (event_id) REFERENCES events (id),
    CONSTRAINT fk_reg_user  FOREIGN KEY (user_id)  REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. od_requests
CREATE TABLE IF NOT EXISTS od_requests (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT          NOT NULL,
    event_id      INT          NOT NULL,
    faculty_id    INT          NULL,
    reason        VARCHAR(500) NULL,
    status        VARCHAR(20)  NULL DEFAULT 'Pending',
    requested_at  DATETIME     NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at    DATETIME     NULL,
    KEY idx_od_user (user_id),
    KEY idx_od_event (event_id),
    KEY idx_od_faculty (faculty_id),
    CONSTRAINT fk_od_user    FOREIGN KEY (user_id)    REFERENCES users (id),
    CONSTRAINT fk_od_event   FOREIGN KEY (event_id)   REFERENCES events (id),
    CONSTRAINT fk_od_faculty FOREIGN KEY (faculty_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. announcements
CREATE TABLE IF NOT EXISTS announcements (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    event_id      INT           NULL,
    organizer_id  INT           NOT NULL,
    title         VARCHAR(255)  NOT NULL,
    body          VARCHAR(1000) NOT NULL,
    created_at    DATETIME      NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_ann_event (event_id),
    KEY idx_ann_organizer (organizer_id),
    CONSTRAINT fk_ann_event     FOREIGN KEY (event_id)     REFERENCES events (id),
    CONSTRAINT fk_ann_organizer FOREIGN KEY (organizer_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. messages
CREATE TABLE IF NOT EXISTS messages (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    conversation_key  VARCHAR(40)   NOT NULL,
    sender_id         INT           NOT NULL,
    receiver_id       INT           NOT NULL,
    text              VARCHAR(2000) NOT NULL,
    is_read           TINYINT(1)    NOT NULL DEFAULT 0,
    created_at        DATETIME      NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_msg_conv (conversation_key),
    KEY idx_msg_sender (sender_id),
    KEY idx_msg_receiver (receiver_id),
    CONSTRAINT fk_msg_sender   FOREIGN KEY (sender_id)   REFERENCES users (id),
    CONSTRAINT fk_msg_receiver FOREIGN KEY (receiver_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. notifications
CREATE TABLE IF NOT EXISTS notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT           NOT NULL,
    title       VARCHAR(255)  NOT NULL,
    body        VARCHAR(1000) NOT NULL,
    icon        VARCHAR(50)   NULL,
    color       VARCHAR(20)   NULL,
    is_read     TINYINT(1)    NOT NULL DEFAULT 0,
    created_at  DATETIME      NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_notif_user (user_id),
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. feedback
CREATE TABLE IF NOT EXISTS feedback (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    event_id    INT           NOT NULL,
    user_id     INT           NOT NULL,
    rating      INT           NOT NULL,
    comment     VARCHAR(1000) NULL,
    created_at  DATETIME      NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_fb_event (event_id),
    KEY idx_fb_user (user_id),
    CONSTRAINT fk_fb_event FOREIGN KEY (event_id) REFERENCES events (id),
    CONSTRAINT fk_fb_user  FOREIGN KEY (user_id)  REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
