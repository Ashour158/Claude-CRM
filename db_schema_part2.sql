-- ========================================
-- DATABASE SCHEMA PART 2
-- Activities, Products, Quote-to-Cash
-- ========================================

-- ========================================
-- ACTIVITIES & TASKS
-- ========================================

-- Activities (Calls, Emails, Meetings, Notes)
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Activity Type
    activity_type VARCHAR(50) NOT NULL, -- 'call', 'email', 'meeting', 'note', 'task'
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Relationships (polymorphic - can relate to any entity)
    related_to_type VARCHAR(50), -- 'lead', 'contact', 'account', 'deal'
    related_to_id UUID,
    
    -- Additional contacts
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    
    -- Timing
    activity_date TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Call specific
    call_direction VARCHAR(20), -- 'inbound', 'outbound'
    call_result VARCHAR(100), -- 'connected', 'voicemail', 'no_answer', 'busy'
    
    -- Email specific
    email_from VARCHAR(255),
    email_to TEXT[], -- Array of email addresses
    email_cc TEXT[],
    email_message_id VARCHAR(255),
    
    -- Meeting specific
    location VARCHAR(255),
    attendees JSONB, -- Array of attendee objects
    
    -- Assignment
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'completed', -- 'planned', 'completed', 'cancelled'
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_activities_company ON activities(company_id);
CREATE INDEX idx_activities_type ON activities(activity_type);
CREATE INDEX idx_activities_related ON activities(related_to_type, related_to_id);
CREATE INDEX idx_activities_date ON activities(activity_date);
CREATE INDEX idx_activities_owner ON activities(owner_id);

-- Enable RLS
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY activities_company_isolation ON activities
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic Info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Relationships
    related_to_type VARCHAR(50), -- 'lead', 'contact', 'account', 'deal'
    related_to_id UUID,
    
    -- Assignment
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timing
    due_date DATE,
    due_time TIME,
    reminder_at TIMESTAMP,
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
    completed_at TIMESTAMP,
    
    -- Recurrence
    is_recurring BOOLEAN DEFAULT false,
    recurrence_pattern JSONB,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_tasks_company ON tasks(company_id);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_related ON tasks(related_to_type, related_to_id);

-- Enable RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tasks_company_isolation ON tasks
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Events (Calendar)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    
    -- Timing
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    is_all_day BOOLEAN DEFAULT false,
    timezone VARCHAR(50),
    
    -- Relationships
    related_to_type VARCHAR(50),
    related_to_id UUID,
    
    -- Attendees
    organizer_id UUID REFERENCES users(id),
    attendees JSONB, -- Array of user/contact objects
    
    -- Recurrence
    is_recurring BOOLEAN DEFAULT false,
    recurrence_pattern JSONB,
    
    -- Reminders
    reminders JSONB, -- Array of reminder objects
    
    -- Status
    status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'cancelled'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_events_company ON events(company_id);
CREATE INDEX idx_events_start ON events(start_datetime);
CREATE INDEX idx_events_organizer ON events(organizer_id);

-- Enable RLS
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

CREATE POLICY events_company_isolation ON events
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- ========================================
-- PRODUCTS & PRICING
-- ========================================

-- Product Categories
CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    description TEXT,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(company_id, name)
);

CREATE INDEX idx_product_categories_company ON product_categories(company_id);
CREATE INDEX idx_product_categories_parent ON product_categories(parent_id);

-- Products
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic Info
    product_code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Category
    category_id UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    
    -- Pricing
    unit_price DECIMAL(15,2) NOT NULL DEFAULT 0,
    cost_price DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Units
    unit_of_measure VARCHAR(50) DEFAULT 'Each', -- 'Each', 'Box', 'Kg', 'Liter', etc.
    
    -- Inventory (basic)
    track_inventory BOOLEAN DEFAULT false,
    quantity_in_stock DECIMAL(15,2) DEFAULT 0,
    reorder_level DECIMAL(15,2),
    
    -- Product Type
    product_type VARCHAR(50) DEFAULT 'physical', -- 'physical', 'service', 'digital'
    
    -- Tax
    is_taxable BOOLEAN DEFAULT true,
    tax_rate DECIMAL(5,2),
    
    -- Attributes (for variants)
    attributes JSONB,
    
    -- Images & Documents
    image_url TEXT,
    documents JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Custom Fields
    custom_fields JSONB,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    UNIQUE(company_id, product_code)
);

CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_code ON products(product_code);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);

-- Enable RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY products_company_isolation ON products
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Price Lists (Territory-based pricing)
CREATE TABLE price_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Territory-based
    territory_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    
    -- Customer-based
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    
    -- Date Range
    valid_from DATE,
    valid_to DATE,
    
    currency VARCHAR(3) DEFAULT 'USD',
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_price_lists_company ON price_lists(company_id);
CREATE INDEX idx_price_lists_territory ON price_lists(territory_id);

-- Price List Items
CREATE TABLE price_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    price_list_id UUID NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    
    unit_price DECIMAL(15,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Quantity-based pricing
    min_quantity DECIMAL(15,2) DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(price_list_id, product_id, min_quantity)
);

CREATE INDEX idx_price_list_items_list ON price_list_items(price_list_id);
CREATE INDEX idx_price_list_items_product ON price_list_items(product_id);

-- ========================================
-- QUOTE-TO-CASH: RFQ & QUOTES
-- ========================================

-- RFQ (Request for Quote) - Field Sales
CREATE TABLE rfqs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    rfq_number VARCHAR(100) UNIQUE NOT NULL,
    
    -- Customer
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    
    -- Territory
    territory_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'submitted', 'under_review', 'converted_to_quote', 'rejected'
    
    -- Notes
    notes TEXT,
    
    -- Assignment
    requested_by UUID REFERENCES users(id), -- Field sales person
    assigned_to UUID REFERENCES users(id), -- Internal sales person
    
    -- Audit
    submitted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_rfqs_company ON rfqs(company_id);
CREATE INDEX idx_rfqs_status ON rfqs(status);
CREATE INDEX idx_rfqs_account ON rfqs(account_id);
CREATE INDEX idx_rfqs_requested_by ON rfqs(requested_by);

-- Enable RLS
ALTER TABLE rfqs ENABLE ROW LEVEL SECURITY;

CREATE POLICY rfqs_company_isolation ON rfqs
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- RFQ Line Items
CREATE TABLE rfq_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rfq_id UUID NOT NULL REFERENCES rfqs(id) ON DELETE CASCADE,
    
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    
    -- Product Details (copied at time of RFQ)
    product_name VARCHAR(255),
    product_code VARCHAR(100),
    description TEXT,
    
    quantity DECIMAL(15,2) NOT NULL,
    unit_of_measure VARCHAR(50),
    
    -- Suggested price (shown to field sales)
    suggested_price DECIMAL(15,2),
    
    notes TEXT,
    
    line_order INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rfq_items_rfq ON rfq_items(rfq_id);
CREATE INDEX idx_rfq_items_product ON rfq_items(product_id);

-- Quotes
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    quote_number VARCHAR(100) UNIQUE NOT NULL,
    
    -- Source
    rfq_id UUID REFERENCES rfqs(id) ON DELETE SET NULL,
    deal_id UUID REFERENCES deals(id) ON DELETE SET NULL,
    
    -- Customer
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    billing_contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    
    -- Territory
    territory_id UUID REFERENCES territories(id) ON DELETE SET NULL,
    
    -- Dates
    quote_date DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'pending_approval', 'approved', 'sent', 'accepted', 'rejected', 'expired'
    
    -- Pricing
    subtotal DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    shipping_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Addresses
    billing_address JSONB,
    shipping_address JSONB,
    
    -- Terms
    payment_terms INTEGER DEFAULT 30, -- Days
    terms_and_conditions TEXT,
    notes TEXT,
    
    -- Template
    template_id UUID, -- Reference to quote template
    
    -- Version Control
    version INTEGER DEFAULT 1,
    parent_quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
    
    -- Assignment
    owner_id UUID REFERENCES users(id),
    
    -- Approval
    requires_approval BOOLEAN DEFAULT false,
    approval_status VARCHAR(50), -- 'pending', 'approved', 'rejected'
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    
    -- Conversion
    converted_to_order BOOLEAN DEFAULT false,
    order_id UUID,
    
    -- Audit
    sent_at TIMESTAMP,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_quotes_company ON quotes(company_id);
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_quotes_account ON quotes(account_id);
CREATE INDEX idx_quotes_deal ON quotes(deal_id);
CREATE INDEX idx_quotes_rfq ON quotes(rfq_id);
CREATE INDEX idx_quotes_owner ON quotes(owner_id);

-- Enable RLS
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY quotes_company_isolation ON quotes
    USING (company_id IN (
        SELECT company_id FROM user_company_access 
        WHERE user_id = current_setting('app.current_user_id')::UUID 
        AND is_active = true
    ));

-- Quote Line Items
CREATE TABLE quote_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    
    -- Product Details (frozen at quote time)
    product_code VARCHAR(100),
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    quantity DECIMAL(15,2) NOT NULL,
    unit_of_measure VARCHAR(50),
    unit_price DECIMAL(15,2) NOT NULL,
    
    -- Discounts
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Tax
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Totals
    line_total DECIMAL(15,2) GENERATED ALWAYS AS (
        (quantity * unit_price) - discount_amount
    ) STORED,
    
    line_order INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quote_items_quote ON quote_items(quote_id);
CREATE INDEX idx_quote_items_product ON quote_items(product_id);

-- Quote Approval Workflow
CREATE TABLE quote_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    
    -- Approval Level
    approval_level INTEGER NOT NULL, -- 1, 2, 3, etc. (sequential)
    approver_id UUID NOT NULL REFERENCES users(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    
    comments TEXT,
    
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quote_approvals_quote ON quote_approvals(quote_id);
CREATE INDEX idx_quote_approvals_approver ON quote_approvals(approver_id);
CREATE INDEX idx_quote_approvals_status ON quote_approvals(status);

-- Quote Templates
CREATE TABLE quote_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Template Content (HTML with variables)
    html_template TEXT NOT NULL,
    css_styles TEXT,
    
    -- Settings
    header_html TEXT,
    footer_html TEXT,
    
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_quote_templates_company ON quote_templates(company_id);

-- ========================================
-- TO BE CONTINUED IN PART 3...
-- Next: Sales Orders, Vendors, Purchase Orders
-- ========================================