-- PostgreSQL Schema for YouTube Studio Analytics
-- This schema stores all YouTube analytics data, accounts, channels, and scraping history

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    cookies_file VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    channel_id VARCHAR(50),
    channel_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_id, channel_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_channels_account_id ON channels(account_id);
CREATE INDEX IF NOT EXISTS idx_channels_url ON channels(url);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(11) UNIQUE NOT NULL,
    channel_id INTEGER REFERENCES channels(id) ON DELETE SET NULL,
    title VARCHAR(500),
    publish_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);

-- Main analytics table
CREATE TABLE IF NOT EXISTS video_analytics (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(11) NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,

    -- Numeric metrics (stored for aggregation and querying)
    impressions INTEGER,
    views INTEGER,
    unique_viewers INTEGER,
    ctr_percentage NUMERIC(5,2),
    views_from_impressions INTEGER,
    youtube_recommending_percentage NUMERIC(5,2),
    ctr_from_impressions_percentage NUMERIC(5,2),
    avg_view_duration_seconds INTEGER,
    watch_time_hours NUMERIC(10,2),

    -- Dates
    publish_start_date DATE,
    scraped_at TIMESTAMP DEFAULT NOW(),

    -- Raw JSON data (for flexibility and debugging)
    top_metrics JSONB,
    traffic_sources JSONB,
    impressions_data JSONB,
    page_text TEXT,

    UNIQUE(video_id, account_id, scraped_at),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_video_analytics_video_id ON video_analytics(video_id);
CREATE INDEX IF NOT EXISTS idx_video_analytics_account_id ON video_analytics(account_id);
CREATE INDEX IF NOT EXISTS idx_video_analytics_scraped_at ON video_analytics(scraped_at);
CREATE INDEX IF NOT EXISTS idx_video_analytics_video_account ON video_analytics(video_id, account_id);

-- Traffic sources (normalized breakdown)
CREATE TABLE IF NOT EXISTS traffic_sources (
    id SERIAL PRIMARY KEY,
    analytics_id INTEGER NOT NULL REFERENCES video_analytics(id) ON DELETE CASCADE,
    source_name VARCHAR(100),
    percentage NUMERIC(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traffic_sources_analytics_id ON traffic_sources(analytics_id);
CREATE INDEX IF NOT EXISTS idx_traffic_sources_source_name ON traffic_sources(source_name);

-- Scraping history/tracker
CREATE TABLE IF NOT EXISTS scraping_history (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(11) REFERENCES videos(video_id) ON DELETE SET NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'success', 'failed', 'skipped', 'pending'
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraping_history_video_account ON scraping_history(video_id, account_id);
CREATE INDEX IF NOT EXISTS idx_scraping_history_status ON scraping_history(status);
CREATE INDEX IF NOT EXISTS idx_scraping_history_created_at ON scraping_history(created_at);
