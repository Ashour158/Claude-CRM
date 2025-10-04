-- ========================================
-- MULTI-TENANT ENTERPRISE CRM DATABASE SCHEMA
-- PostgreSQL 14+ with Row-Level Security
-- ========================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================
-- CORE MULTI-TENANT TABLES
-- ========================================

-- Companies (Tenant Anchor Table)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    code VARCHAR(50) UNIQUE NOT NULL,
    tax_id VARCHAR(100),
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    
    -- Settings
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    fiscal_year_start_month INTEGER DEFAULT 1,
    
    -- Logo and Branding
    logo_url TEXT,
    primary_color VARCHAR(7) DEFAULT '#0066CC',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    subscription_plan VARCHAR(50),
    subscription_expires_at TIMESTAMP,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

CREATE INDEX idx_companies_code ON companies(code);
CREATE INDEX idx_companies_active ON companies(is_active);

-- ========================================
-- USERS & AUTHENTICATION
-- ========================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Personal Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    
    -- Profile
    avatar_url TEXT,
    title VARCHAR(100),
    department VARCHAR(100),
    
    -- Authentication
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    
    -- Two-Factor Authentication
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    
    -- Session Management
    last_login_at TIMESTAMP,
    last_login_ip INET,
    login_count INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_superadmin BOOLEAN DEFAULT false,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- User Company Access (Many-to-Many)
CREATE TABLE user_company_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Role in this company
    role VARCHAR(50) NOT NULL, -- 'admin', 'manager', 'sales_rep', 'viewer'
    
    -- Permissions
    can_create BOOLEAN DEFAULT true,
    can_read BOOLEAN DEFAULT true,
    can_update BOOLEAN DEFAULT true,
    can_delete BOOLEAN DEFAULT false,
    can_export BOOLEAN DEFAULT false,
    
    -- Status
    is_primary BOOLEAN DEFAULT false, -- Primary company for this user
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    
    UNIQUE(user_id, company_id)
);

CREATE INDEX idx_uca_user ON user_company_access(user_id);
CREATE INDEX idx_uca_company ON user_company_access(company_id);
CREATE INDEX idx_uca_active ON user_company_access(is_active);

-- User Sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL UNIQUE,
    refresh_token VARCHAR(500),
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(token);

-- ========================================
-- TERRITORY MANAGEMENT
-- ========================================

CREATE TABLE territories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Hierarchy
    parent_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Territory Type
    type VARCHAR(50) NOT NULL, -- 'geographic', 'product', 'customer_segment', 'industry'
    
    -- Manager
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Geographic Criteria (if type = geographic)
    countries TEXT[], -- Array of country codes
    states TEXT[],
    cities TEXT[],
    postal_codes TEXT[],
    
    -- Product Criteria (if type = product)
    product_categories TEXT[],
    product_ids UUID[],
    
    -- Customer Criteria (if type = customer_segment)
    customer_types TEXT[], -- 'enterprise', 'smb', 'startup'
    revenue_min DECIMAL(15,2),
    revenue_max DECIMAL(15,2),
    industries TEXT[],
    
    -- Settings
    currency VARCHAR(3),
    quota_amount DECIMAL(15,2),
    quota_period VARCHAR(20), -- 'monthly', 'quarterly', 'annual'
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    UNIQUE(company_id, code)
);

CREATE INDEX idx_territories_company ON territories(company_id);
CREATE INDEX idx_territories_parent ON territories(parent_id);
CREATE INDEX idx_territories_manager ON territories(manager_id);
CREATE INDEX idx_territories_type ON territories(type);

-- Territory Assignment Rules
CREATE TABLE territory_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    territory_id UUID NOT NULL REFERENCES territories(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 0, -- Higher priority rules run first
    
    -- Conditions (JSON for flexible criteria)
    conditions JSONB NOT NULL,
    -- Example: {"field": "account.country", "operator": "in", "value": ["US", "CA"]}
    
    -- Assignment
    auto_assign BOOLEAN DEFAULT true,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_territory_rules_company ON territory_rules(company_id);
CREATE INDEX idx_territory_rules_territory ON territory_rules(territory_id);
CREATE INDEX idx_territory_rules_priority ON territory_rules(priority DESC);

-- ========================================
-- CRM CORE ENTITIES
-- ========================================

-- Accounts (Companies/Organizations)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    account_number VARCHAR(100) UNIQUE,
    website VARCHAR(255),
    
    -- Type and Status
    account_type VARCHAR(50), -- 'customer', 'prospect', 'partner', 'competitor'
    industry VARCHAR(100),
    annual_revenue DECIMAL(15,2),
    employee_count INTEGER,
    
    -- Contact Information
    phone VARCHAR(50),
    email VARCHAR(255),
    
    -- Address
    billing_address_line1 VARCHAR(255),
    billing_address_line2 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(100),
    billing_postal_code VARCHAR(20),
    billing_country VARCHAR(100),
    
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(100),
    
    -- Relationships
    parent_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    territory_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Settings
    payment_terms INTEGER DEFAULT 30, -- Days
    credit_limit DECIMAL(15,2),
    tax_id VARCHAR(100),
    
    -- Custom Fields (JSONB for flexibility)
    custom_fields JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_accounts_company ON accounts(company_id);
CREATE INDEX idx_accounts_territory ON accounts(territory_id);
CREATE INDEX idx_accounts_owner ON accounts(owner_id);
CREATE INDEX idx_accounts_type ON accounts(account_type);

-- Enable RLS
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see accounts in their companies
CREATE POLICY accounts_company_isolation ON accounts
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Contacts (People)
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    title VARCHAR(100),
    department VARCHAR(100),
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    
    -- Social
    linkedin_url VARCHAR(255),
    twitter_handle VARCHAR(100),
    
    -- Relationships
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    reports_to_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Address (inherits from account or custom)
    mailing_address_line1 VARCHAR(255),
    mailing_address_line2 VARCHAR(255),
    mailing_city VARCHAR(100),
    mailing_state VARCHAR(100),
    mailing_postal_code VARCHAR(20),
    mailing_country VARCHAR(100),
    
    -- Preferences
    email_opt_out BOOLEAN DEFAULT false,
    do_not_call BOOLEAN DEFAULT false,
    
    -- Custom Fields
    custom_fields JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_account ON contacts(account_id);
CREATE INDEX idx_contacts_owner ON contacts(owner_id);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_name ON contacts(full_name);

-- Enable RLS
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY contacts_company_isolation ON contacts
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Leads
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    title VARCHAR(100),
    company_name VARCHAR(255),
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    website VARCHAR(255),
    
    -- Lead Details
    lead_source VARCHAR(100), -- 'website', 'referral', 'cold_call', 'trade_show', etc.
    lead_status VARCHAR(50) DEFAULT 'new', -- 'new', 'contacted', 'qualified', 'unqualified', 'converted'
    rating VARCHAR(20), -- 'hot', 'warm', 'cold'
    
    -- Scoring
    lead_score INTEGER DEFAULT 0,
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    
    -- Business Info
    industry VARCHAR(100),
    annual_revenue DECIMAL(15,2),
    employee_count INTEGER,
    
    -- Relationships
    territory_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Conversion
    converted_at TIMESTAMP,
    converted_account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    converted_contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    converted_deal_id UUID,
    
    -- Description
    description TEXT,
    
    -- Custom Fields
    custom_fields JSONB,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_leads_company ON leads(company_id);
CREATE INDEX idx_leads_owner ON leads(owner_id);
CREATE INDEX idx_leads_status ON leads(lead_status);
CREATE INDEX idx_leads_territory ON leads(territory_id);
CREATE INDEX idx_leads_email ON leads(email);

-- Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY leads_company_isolation ON leads
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Pipeline Stages
CREATE TABLE pipeline_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    probability INTEGER DEFAULT 0, -- 0-100%
    stage_order INTEGER NOT NULL,
    
    -- Classification
    is_won BOOLEAN DEFAULT false,
    is_lost BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(company_id, name)
);

CREATE INDEX idx_pipeline_stages_company ON pipeline_stages(company_id);

-- Deals/Opportunities
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    deal_number VARCHAR(100) UNIQUE,
    
    -- Value
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Pipeline
    stage_id UUID REFERENCES pipeline_stages(id) ON DELETE SET NULL,
    probability INTEGER DEFAULT 0, -- 0-100%
    
    -- Dates
    close_date DATE,
    actual_close_date DATE,
    
    -- Relationships
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    territory_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Classification
    deal_type VARCHAR(50), -- 'new_business', 'existing_business', 'renewal'
    lead_source VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'open', -- 'open', 'won', 'lost', 'abandoned'
    lost_reason VARCHAR(255),
    
    -- Description
    description TEXT,
    next_step TEXT,
    
    -- Custom Fields
    custom_fields JSONB,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_deals_company ON deals(company_id);
CREATE INDEX idx_deals_stage ON deals(stage_id);
CREATE INDEX idx_deals_account ON deals(account_id);
CREATE INDEX idx_deals_owner ON deals(owner_id);
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_close_date ON deals(close_date);

-- Enable RLS
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;

CREATE POLICY deals_company_isolation ON deals
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- ========================================
-- TO BE CONTINUED IN NEXT FILES...
-- This is Part 1 of the schema
-- Next parts will include:
-- - Activities, Tasks, Events
-- - Products, Price Lists
-- - Quotes, RFQs, Sales Orders
-- - Vendors, Purchase Orders
-- - Custom Fields
-- - Audit Logs
-- ========================================