import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle, Circle, Clock, AlertCircle } from 'lucide-react';

const EnterpriseERPProjectPlan = () => {
  const [expandedPhases, setExpandedPhases] = useState({});
  const [completedTasks, setCompletedTasks] = useState({});
  const [selectedPhase, setSelectedPhase] = useState(null);

  const projectPlan = {
    projectName: "Enterprise Multi-Tenant CRM System",
    subtitle: "Zoho CRM Enhanced with Multi-Company, Territory Management & Procurement",
    timeline: "12-24 months",
    teamSize: "4-6 developers (or solo with 5-6 hours daily)",
    phases: [
      {
        id: 1,
        name: "Foundation & Architecture Setup",
        duration: "4 weeks",
        weeks: "Week 1-4",
        priority: "Critical",
        status: "pending",
        description: "Set up multi-tenant architecture, development environment, and core database design",
        tasks: [
          {
            id: "1.1",
            name: "Multi-Tenant Architecture Design",
            priority: "Critical",
            subtasks: [
              "Design PostgreSQL Row-Level Security (RLS) architecture",
              "Create company isolation strategy (shared database approach)",
              "Design user-to-company access mapping (many-to-many)",
              "Plan company switching mechanism in UI",
              "Design data partitioning strategy for performance",
              "Create security policies for tenant isolation"
            ]
          },
          {
            id: "1.2",
            name: "Technology Stack Setup",
            priority: "Critical",
            subtasks: [
              "Install Python 3.11+ and Django 4.2+",
              "Set up PostgreSQL 14+ with RLS enabled",
              "Install Redis 7+ for caching and sessions",
              "Initialize React 18+ with TypeScript project",
              "Set up Django REST Framework",
              "Configure Celery for background tasks",
              "Install document generation libraries (WeasyPrint/ReportLab)"
            ]
          },
          {
            id: "1.3",
            name: "Core Database Schema Design",
            priority: "Critical",
            subtasks: [
              "Design Companies table (multi-tenant anchor)",
              "Design Users table with role-based access",
              "Design UserCompanyAccess (many-to-many mapping)",
              "Design Territories table with hierarchy support",
              "Create base models with company_id for RLS",
              "Design audit trail tables (who changed what, when)",
              "Create database migration strategy"
            ]
          },
          {
            id: "1.4",
            name: "Development Environment",
            priority: "High",
            subtasks: [
              "Set up Git repository structure (monorepo vs separate repos)",
              "Create Docker containers for development",
              "Set up VS Code with recommended extensions",
              "Configure pre-commit hooks and linting",
              "Create development database with sample companies",
              "Set up API documentation (Swagger/OpenAPI)",
              "Create project documentation wiki"
            ]
          }
        ]
      },
      {
        id: 2,
        name: "Authentication & Multi-Tenancy Core",
        duration: "3 weeks",
        weeks: "Week 5-7",
        priority: "Critical",
        status: "pending",
        description: "Build authentication system with multi-company access and role-based permissions",
        tasks: [
          {
            id: "2.1",
            name: "Authentication System",
            priority: "Critical",
            subtasks: [
              "User registration with email verification",
              "Login/logout with JWT tokens",
              "Password reset functionality",
              "Two-factor authentication (2FA) optional",
              "Session management with Redis",
              "API authentication middleware",
              "Remember me functionality"
            ]
          },
          {
            id: "2.2",
            name: "Multi-Company Access Control",
            priority: "Critical",
            subtasks: [
              "Implement company switching mechanism",
              "Create middleware to set active company context",
              "Build user-company permission matrix",
              "Implement PostgreSQL RLS policies per table",
              "Create company-scoped queries automatically",
              "Add company selector UI component",
              "Test data isolation between companies"
            ]
          },
          {
            id: "2.3",
            name: "Role-Based Access Control (RBAC)",
            priority: "Critical",
            subtasks: [
              "Define roles: Super Admin, Admin, Sales Manager, Sales Rep, Viewer",
              "Create permission system (CRUD per module)",
              "Implement role inheritance",
              "Build permission decorator for API endpoints",
              "Create UI for role management (Admin only)",
              "Test permission enforcement across modules"
            ]
          },
          {
            id: "2.4",
            name: "Company Management Module",
            priority: "High",
            subtasks: [
              "CRUD operations for companies (Super Admin only)",
              "Company profile (name, address, logo, settings)",
              "Assign users to companies with roles",
              "Company-specific settings (currency, timezone, fiscal year)",
              "Company deactivation/archival"
            ]
          }
        ]
      },
      {
        id: 3,
        name: "Core CRM Modules - Foundation",
        duration: "6 weeks",
        weeks: "Week 8-13",
        priority: "High",
        status: "pending",
        description: "Build fundamental CRM modules: Contacts, Accounts, Leads, Activities",
        tasks: [
          {
            id: "3.1",
            name: "Contacts Module",
            priority: "High",
            subtasks: [
              "Contact database model (name, email, phone, title, etc.)",
              "CRUD API endpoints with company isolation",
              "Contact list view with search, filter, sort",
              "Contact detail page with activity timeline",
              "Import contacts from CSV",
              "Export contacts to CSV/Excel",
              "Contact deduplication logic",
              "Contact custom fields (up to 50 per company)",
              "Contact tags and categories"
            ]
          },
          {
            id: "3.2",
            name: "Accounts Module",
            priority: "High",
            subtasks: [
              "Account/Company database model",
              "Link multiple contacts to one account",
              "Account hierarchy (parent-child relationships)",
              "Account CRUD with company isolation",
              "Account types (customer, prospect, partner, competitor)",
              "Account revenue tracking",
              "Account custom fields"
            ]
          },
          {
            id: "3.3",
            name: "Leads Module",
            priority: "High",
            subtasks: [
              "Lead database model with pipeline stages",
              "Lead source tracking (website, referral, cold call, etc.)",
              "Lead qualification criteria",
              "Convert lead to contact/account/deal workflow",
              "Lead assignment rules (manual and automatic)",
              "Lead scoring system (basic)",
              "Lead custom fields",
              "Duplicate lead detection"
            ]
          },
          {
            id: "3.4",
            name: "Activities Module",
            priority: "High",
            subtasks: [
              "Activity types: Call, Email, Meeting, Note, Task",
              "Log activity against contact/account/lead/deal",
              "Activity timeline view (chronological)",
              "Activity filters (by type, date, user)",
              "Activity reminders and notifications",
              "Bulk activity logging",
              "Activity reporting"
            ]
          }
        ]
      },
      {
        id: 4,
        name: "Territory Management System",
        duration: "5 weeks",
        weeks: "Week 14-18",
        priority: "High",
        status: "pending",
        description: "Build comprehensive territory management with hierarchies, rules, and assignment automation",
        tasks: [
          {
            id: "4.1",
            name: "Territory Hierarchy & Structure",
            priority: "Critical",
            subtasks: [
              "Territory database model with unlimited hierarchy depth",
              "Territory types: Geographic, Product-based, Customer segment",
              "Visual territory hierarchy builder (drag-drop tree)",
              "Territory parent-child relationships",
              "Territory code/naming system",
              "Territory manager assignment",
              "Territory activation/deactivation"
            ]
          },
          {
            id: "4.2",
            name: "Territory Assignment Rules",
            priority: "High",
            subtasks: [
              "Rule engine for automatic territory assignment",
              "Assignment criteria: Location (zip/city/state/country), Industry, Company size, Revenue range",
              "Multiple overlapping territories support",
              "Primary vs secondary territory designation",
              "Territory transfer workflows",
              "Territory conflict resolution rules"
            ]
          },
          {
            id: "4.3",
            name: "Territory-Based Pricing",
            priority: "High",
            subtasks: [
              "Price lists per territory",
              "Territory-specific discount rules",
              "Currency per territory",
              "Price override permissions by territory",
              "Pricing tier by territory (premium, standard, economy)"
            ]
          },
          {
            id: "4.4",
            name: "Territory Performance & Reporting",
            priority: "Medium",
            subtasks: [
              "Territory revenue dashboard",
              "Territory quota tracking",
              "Territory win rate analytics",
              "Territory pipeline coverage",
              "Territory comparison reports",
              "Territory heat maps (visual geographic representation)"
            ]
          }
        ]
      },
      {
        id: 5,
        name: "Deals & Pipeline Management",
        duration: "4 weeks",
        weeks: "Week 19-22",
        priority: "High",
        status: "pending",
        description: "Sales pipeline with customizable stages, forecasting, and deal tracking",
        tasks: [
          {
            id: "5.1",
            name: "Deals/Opportunities Module",
            priority: "High",
            subtasks: [
              "Deal database model (value, probability, close date)",
              "Link deal to account and contact",
              "Deal stages (customizable per company)",
              "Deal stage movement tracking (audit trail)",
              "Deal products/line items",
              "Deal team members (multiple users per deal)",
              "Deal custom fields",
              "Deal notes and attachments"
            ]
          },
          {
            id: "5.2",
            name: "Pipeline Management",
            priority: "High",
            subtasks: [
              "Kanban board view (drag-drop between stages)",
              "Pipeline value calculation per stage",
              "Weighted pipeline (value × probability)",
              "Multiple pipelines support (different sales processes)",
              "Pipeline filters (by user, territory, date, product)",
              "Pipeline velocity metrics",
              "Stale deal alerts (deals stuck in stage)"
            ]
          },
          {
            id: "5.3",
            name: "Sales Forecasting",
            priority: "High",
            subtasks: [
              "Forecast by time period (monthly, quarterly, yearly)",
              "Forecast by territory hierarchy",
              "Forecast by product line",
              "Forecast categories: Best case, Most likely, Worst case",
              "Forecast vs actual tracking",
              "Historical forecast accuracy",
              "AI-based forecast prediction (optional, Phase 2)"
            ]
          },
          {
            id: "5.4",
            name: "Quota & Target Management",
            priority: "Medium",
            subtasks: [
              "Set quotas by user, team, territory",
              "Quota periods (monthly, quarterly, annual)",
              "Quota vs achievement tracking",
              "Quota attainment percentage",
              "Quota rollup (team to territory to company)",
              "Visual quota dashboards"
            ]
          }
        ]
      },
      {
        id: 6,
        name: "Quote-to-Cash: RFQ & Quotation System",
        duration: "6 weeks",
        weeks: "Week 23-28",
        priority: "Critical",
        status: "pending",
        description: "Complete RFQ workflow with custom templates, approval workflows, and quote generation",
        tasks: [
          {
            id: "6.1",
            name: "Product Catalog",
            priority: "High",
            subtasks: [
              "Product database (SKU, name, description, category)",
              "Product pricing (base price, cost, margin)",
              "Product variants (size, color, etc.)",
              "Product units of measure",
              "Product active/inactive status",
              "Product images and documents",
              "Product custom fields"
            ]
          },
          {
            id: "6.2",
            name: "RFQ (Request for Quote) Module - Field Sales",
            priority: "Critical",
            subtasks: [
              "RFQ creation form (simple product selection)",
              "Product search and add to RFQ",
              "Quantity and notes per product",
              "RFQ saved as draft or submitted",
              "View suggested prices based on territory/customer",
              "RFQ submission triggers notification to internal sales",
              "RFQ status tracking (draft, submitted, under review)"
            ]
          },
          {
            id: "6.3",
            name: "Quote Generation & Management",
            priority: "Critical",
            subtasks: [
              "Convert RFQ to Quote",
              "Quote line items with pricing",
              "Apply discounts (percentage or fixed amount)",
              "Calculate totals (subtotal, tax, shipping, total)",
              "Quote validity period (expiration date)",
              "Quote terms and conditions",
              "Quote versions (track revisions)",
              "Quote templates (multiple layouts)"
            ]
          },
          {
            id: "6.4",
            name: "Custom Template Engine",
            priority: "Critical",
            subtasks: [
              "Upload custom quote templates (HTML/CSS)",
              "Template variables system ({{company_name}}, {{total}}, etc.)",
              "Template preview functionality",
              "Multiple templates per company",
              "Default template selection",
              "Generate PDF from template + data",
              "Email quote PDF to customer",
              "Customer portal to view/accept quotes (optional)"
            ]
          },
          {
            id: "6.5",
            name: "Multi-Level Approval Workflow",
            priority: "Critical",
            subtasks: [
              "Define approval chains (Sales Rep → Manager → Director)",
              "Conditional approvals (e.g., discount > 20% requires Director)",
              "Approval/rejection with comments",
              "Email notifications for pending approvals",
              "Approval history and audit trail",
              "Parallel vs sequential approvals",
              "Auto-approval rules (within authorized limits)"
            ]
          }
        ]
      },
      {
        id: 7,
        name: "Sales Order & Fulfillment",
        duration: "4 weeks",
        weeks: "Week 29-32",
        priority: "High",
        status: "pending",
        description: "Convert quotes to sales orders and track fulfillment",
        tasks: [
          {
            id: "7.1",
            name: "Sales Order Module",
            priority: "High",
            subtasks: [
              "Auto-create SO when deal marked as Won",
              "SO number generation (customizable format)",
              "SO line items from quote",
              "SO status tracking (pending, confirmed, fulfilled, cancelled)",
              "SO payment terms",
              "SO delivery date and address",
              "SO custom fields",
              "SO PDF generation with custom templates"
            ]
          },
          {
            id: "7.2",
            name: "Order Fulfillment Tracking",
            priority: "Medium",
            subtasks: [
              "Fulfillment status per line item",
              "Partial fulfillment support",
              "Shipping information (carrier, tracking number)",
              "Delivery confirmation",
              "Fulfillment notes",
              "Return/refund tracking (basic)"
            ]
          },
          {
            id: "7.3",
            name: "Invoicing (Basic)",
            priority: "Medium",
            subtasks: [
              "Generate invoice from sales order",
              "Invoice numbering system",
              "Invoice payment status (unpaid, partial, paid)",
              "Invoice due date calculation",
              "Invoice PDF generation",
              "Payment recording",
              "Aging report (30, 60, 90 days)"
            ]
          },
          {
            id: "7.4",
            name: "DSO Calculation & Tracking",
            priority: "High",
            subtasks: [
              "Days Sales Outstanding (DSO) formula implementation",
              "DSO calculation by company/territory",
              "DSO trend over time",
              "Accounts receivable aging report",
              "Payment collection dashboard",
              "Overdue invoice alerts"
            ]
          }
        ]
      },
      {
        id: 8,
        name: "Vendor Management & Procurement",
        duration: "5 weeks",
        weeks: "Week 33-37",
        priority: "High",
        status: "pending",
        description: "Complete vendor management with performance tracking and procurement workflows",
        tasks: [
          {
            id: "8.1",
            name: "Vendor Database",
            priority: "High",
            subtasks: [
              "Vendor master data (name, contact info, address)",
              "Vendor categories (raw materials, services, equipment)",
              "Vendor registration type (LLC, Corp, Sole Proprietor)",
              "Vendor financial information (annual revenue, credit rating)",
              "Vendor certifications and compliance docs",
              "Vendor payment terms",
              "Vendor contact persons (multiple)",
              "Vendor custom fields"
            ]
          },
          {
            id: "8.2",
            name: "Vendor Performance Tracking",
            priority: "High",
            subtasks: [
              "Vendor scorecard system (quality, delivery, price, service)",
              "Automated performance metrics calculation",
              "Vendor rating (1-5 stars)",
              "Vendor lifecycle status (approved, on-hold, blacklisted)",
              "Vendor performance trends over time",
              "Vendor comparison dashboard",
              "Vendor performance alerts (low scores)"
            ]
          },
          {
            id: "8.3",
            name: "Product/Item Performance by Vendor",
            priority: "Medium",
            subtasks: [
              "Track product quality by vendor",
              "Product defect rate per vendor",
              "Product delivery time per vendor",
              "Product cost history per vendor",
              "Preferred vendor designation per product",
              "Alternative vendor suggestions"
            ]
          },
          {
            id: "8.4",
            name: "Purchase Requisition & RFQ to Vendors",
            priority: "High",
            subtasks: [
              "Internal purchase requisition workflow",
              "Send RFQ to multiple vendors (competitive bidding)",
              "Vendor quote comparison",
              "Vendor quote evaluation matrix",
              "Award PO to winning vendor",
              "RFQ response deadline tracking"
            ]
          },
          {
            id: "8.5",
            name: "Purchase Orders",
            priority: "High",
            subtasks: [
              "Create PO from approved RFQ",
              "PO line items with pricing",
              "PO approval workflow",
              "PO status tracking (draft, approved, sent, received, closed)",
              "PO delivery tracking",
              "PO invoice matching (3-way match: PO-Receipt-Invoice)",
              "PO custom templates"
            ]
          }
        ]
      },
      {
        id: 9,
        name: "Reporting, Analytics & Dashboards",
        duration: "4 weeks",
        weeks: "Week 38-41",
        priority: "Medium",
        status: "pending",
        description: "Comprehensive reporting system with visual dashboards and export capabilities",
        tasks: [
          {
            id: "9.1",
            name: "Dashboard Framework",
            priority: "High",
            subtasks: [
              "Role-based dashboards (different views per role)",
              "Customizable dashboard widgets",
              "Drag-drop dashboard builder",
              "Real-time data updates",
              "Dashboard filters (date range, territory, user)",
              "Dashboard export to PDF",
              "Dashboard sharing"
            ]
          },
          {
            id: "9.2",
            name: "Sales Analytics",
            priority: "High",
            subtasks: [
              "Pipeline value and velocity charts",
              "Win/loss rate analysis",
              "Deal stage conversion rates",
              "Sales by territory/product/rep",
              "Quota attainment tracking",
              "Revenue forecasts vs actuals",
              "Sales cycle length analysis"
            ]
          },
          {
            id: "9.3",
            name: "Financial Reports",
            priority: "High",
            subtasks: [
              "DSO report and trends",
              "AR aging report",
              "Revenue by period (monthly, quarterly, yearly)",
              "Profit margin analysis",
              "Payment collection reports",
              "Outstanding invoices summary"
            ]
          },
          {
            id: "9.4",
            name: "Operational Reports",
            priority: "Medium",
            subtasks: [
              "Activity reports (calls, meetings, emails per user)",
              "Lead conversion funnel",
              "Territory performance comparison",
              "Vendor performance scorecards",
              "Product performance reports",
              "User productivity reports"
            ]
          },
          {
            id: "9.5",
            name: "Custom Report Builder",
            priority: "Medium",
            subtasks: [
              "Drag-drop report builder",
              "Select fields from any module",
              "Apply filters and grouping",
              "Chart type selection (bar, line, pie, table)",
              "Save custom reports",
              "Schedule automated report emails",
              "Export to Excel/CSV/PDF"
            ]
          }
        ]
      },
      {
        id: 10,
        name: "Workflow Automation & Email Integration",
        duration: "4 weeks",
        weeks: "Week 42-45",
        priority: "Medium",
        status: "pending",
        description: "Automate repetitive tasks and integrate email communication",
        tasks: [
          {
            id: "10.1",
            name: "Workflow Rules Engine",
            priority: "High",
            subtasks: [
              "Trigger-based workflows (on create, update, time-based)",
              "Condition builder (if-then-else logic)",
              "Actions: Send email, Create task, Update field, Send webhook",
              "Multi-step workflows",
              "Workflow approval steps",
              "Workflow history and logs",
              "Workflow enable/disable toggle"
            ]
          },
          {
            id: "10.2",
            name: "Email Integration",
            priority: "High",
            subtasks: [
              "Connect Gmail/Outlook accounts (OAuth)",
              "Send emails from CRM with tracking",
              "Log emails automatically to CRM records",
              "Email templates library",
              "Email template variables",
              "Email open and click tracking",
              "Email thread preservation",
              "Bulk email sending"
            ]
          },
          {
            id: "10.3",
            name: "Task Automation",
            priority: "Medium",
            subtasks: [
              "Auto-create follow-up tasks based on triggers",
              "Task reminders via email/push notification",
              "Recurring task creation",
              "Task assignment rules",
              "Overdue task escalation",
              "Task completion workflows"
            ]
          },
          {
            id: "10.4",
            name: "Notification System",
            priority: "Medium",
            subtasks: [
              "In-app notifications",
              "Email notifications",
              "Push notifications (mobile)",
              "Notification preferences per user",
              "Notification center UI",
              "Notification grouping and summarization"
            ]
          }
        ]
      },
      {
        id: 11,
        name: "Mobile Responsiveness & UI/UX Polish",
        duration: "3 weeks",
        weeks: "Week 46-48",
        priority: "High",
        status: "pending",
        description: "Ensure excellent mobile experience and polish the user interface",
        tasks: [
          {
            id: "11.1",
            name: "Mobile-Responsive Design",
            priority: "Critical",
            subtasks: [
              "Test all pages on mobile devices",
              "Optimize navigation for touch screens",
              "Mobile-friendly forms and inputs",
              "Responsive tables and charts",
              "Mobile dashboard optimization",
              "Touch gestures (swipe, pinch-to-zoom)"
            ]
          },
          {
            id: "11.2",
            name: "UI/UX Improvements",
            priority: "High",
            subtasks: [
              "Consistent design system across modules",
              "Loading states and skeleton screens",
              "Error handling and user-friendly messages",
              "Empty states with helpful guidance",
              "Tooltips and inline help",
              "Keyboard shortcuts",
              "Dark mode support (optional)"
            ]
          },
          {
            id: "11.3",
            name: "Performance Optimization",
            priority: "High",
            subtasks: [
              "Frontend bundle optimization",
              "Lazy loading for modules",
              "Database query optimization",
              "Add database indexes",
              "Implement caching (Redis)",
              "Image optimization",
              "API response time monitoring"
            ]
          }
        ]
      },
      {
        id: 12,
        name: "Testing & Quality Assurance",
        duration: "4 weeks",
        weeks: "Week 49-52",
        priority: "Critical",
        status: "pending",
        description: "Comprehensive testing across all modules and scenarios",
        tasks: [
          {
            id: "12.1",
            name: "Backend Testing",
            priority: "Critical",
            subtasks: [
              "Unit tests for all models",
              "API endpoint tests (100% coverage goal)",
              "Multi-tenant isolation tests",
              "Permission/authorization tests",
              "Workflow engine tests",
              "Database integrity tests",
              "Load testing (simulate 100+ users)"
            ]
          },
          {
            id: "12.2",
            name: "Frontend Testing",
            priority: "High",
            subtasks: [
              "Component unit tests",
              "Integration tests for key workflows",
              "End-to-end tests (Cypress/Playwright)",
              "Cross-browser testing (Chrome, Firefox, Safari, Edge)",
              "Mobile device testing (iOS, Android)",
              "Accessibility testing (WCAG compliance)"
            ]
          },
          {
            id: "12.3",
            name: "User Acceptance Testing (UAT)",
            priority: "Critical",
            subtasks: [
              "Create test users for each role",
              "Test all workflows end-to-end",
              "RFQ → Quote → Approval → SO → Fulfillment",
              "Multi-company user switching",
              "Territory assignment and pricing",
              "Vendor management workflows",
              "Report generation and export",
              "Collect feedback and fix issues"
            ]
          },
          {
            id: "12.4",
            name: "Security Testing",
            priority: "Critical",
            subtasks: [
              "Penetration testing (basic)",
              "SQL injection prevention verification",
              "XSS attack prevention",
              "CSRF token implementation",
              "Password security audit",
              "Multi-tenant data leak tests",
              "API authentication/authorization tests"
            ]
          }
        ]
      },
      {
        id: 13,
        name: "Deployment & Production Launch",
        duration: "3 weeks",
        weeks: "Week 53-55",
        priority: "Critical",
        status: "pending",
        description: "Deploy to production and launch to users",
        tasks: [
          {
            id: "13.1",
            name: "Production Infrastructure Setup",
            priority: "Critical",
            subtasks: [
              "Choose cloud provider (AWS/Azure/GCP/DigitalOcean)",
              "Set up production servers (app, database, Redis)",
              "Configure load balancer (if needed for 100 users)",
              "Set up SSL certificates (HTTPS)",
              "Configure domain name and DNS",
              "Set up CDN for static assets",
              "Configure backup strategy (daily database backups)"
            ]
          },
          {
            id: "13.2",
            name: "Production Database",
            priority: "Critical",
            subtasks: [
              "Provision production PostgreSQL instance",
              "Run all database migrations",
              "Import master data (products, territories, etc.)",
              "Create initial companies and users",
              "Test database performance",
              "Set up monitoring and alerts"
            ]
          },
          {
            id: "13.3",
            name: "CI/CD Pipeline",
            priority: "High",
            subtasks: [
              "Set up GitHub Actions / GitLab CI",
              "Automated testing on commit",
              "Automated deployment to staging",
              "Manual approval for production deploy",
              "Rollback strategy",
              "Environment variable management"
            ]
          },
          {
            id: "13.4",
            name: "Monitoring & Logging",
            priority: "Critical",
            subtasks: [
              "Application performance monitoring (APM)",
              "Error tracking (Sentry or similar)",
              "Server monitoring (CPU, memory, disk)",
              "Database monitoring (query performance)",
              "User activity logs",
              "Set up alerts for critical errors",
              "Create incident response plan"
            ]
          },
          {
            id: "13.5",
            name: "User Onboarding & Documentation",
            priority: "High",
            subtasks: [
              "Create user documentation (wiki/help center)",
              "Record video tutorials for key features",
              "Create admin guide for system setup",
              "Prepare training materials",
              "Set up support ticketing system",
              "Create FAQ section",
              "Onboard initial 100 users in phases"
            ]
          }
        ]
      },
      {
        id: 14,
        name: "Post-Launch: Monitoring & Iteration",
        duration: "Ongoing",
        weeks: "Week 56+",
        priority: "Medium",
        status: "pending",
        description: "Monitor system performance, gather feedback, and continuously improve",
        tasks: [
          {
            id: "14.1",
            name: "Production Monitoring",
            priority: "Critical",
            subtasks: [
              "Monitor system uptime (99.9% target)",
              "Track response times and performance",
              "Monitor database query performance",
              "Review error logs daily",
              "Track user adoption metrics",
              "Monitor server costs and optimization"
            ]
          },
          {
            id: "14.2",
            name: "User Feedback & Support",
            priority: "High",
            subtasks: [
              "Collect user feedback regularly",
              "Track feature requests",
              "Support ticket resolution",
              "Bug fixes and patches",
              "User satisfaction surveys",
              "Create product roadmap based on feedback"
            ]
          },
          {
            id: "14.3",
            name: "Feature Enhancements (Phase 2)",
            priority: "Medium",
            subtasks: [
              "AI-based lead scoring",
              "Predictive analytics for sales forecasting",
              "Advanced reporting with BI integration",
              "Mobile native apps (iOS/Android)",
              "Third-party integrations (Zapier, etc.)",
              "Advanced workflow automation",
              "Customer portal for quote acceptance",
              "E-signature integration"
            ]
          }
        ]
      }
    ]
  };

  const togglePhase = (phaseId) => {
    setExpandedPhases(prev => ({
      ...prev,
      [phaseId]: !prev[phaseId]
    }));
  };

  const toggleTask = (taskId) => {
    setCompletedTasks(prev => ({
      ...prev,
      [taskId]: !prev[taskId]
    }));
  };

  const getPhaseColor = (priority) => {
    switch(priority) {
      case 'Critical': return 'border-red-500 bg-red-50';
      case 'High': return 'border-orange-500 bg-orange-50';
      case 'Medium': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-300 bg-gray-50';
    }
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      'Critical': 'bg-red-100 text-red-700',
      'High': 'bg-orange-100 text-orange-700',
      'Medium': 'bg-blue-100 text-blue-700'
    };
    return colors[priority] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-xl p-8 mb-6 border-l-8 border-blue-600">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                {projectPlan.projectName}
              </h1>
              <p className="text-lg text-gray-600 mb-4">
                {projectPlan.subtitle}
              </p>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Clock size={18} className="text-blue-600" />
                  <span className="font-semibold text-gray-700">Timeline:</span>
                  <span className="text-gray-600">{projectPlan.timeline}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">Team:</span>
                  <span className="text-gray-600">{projectPlan.teamSize}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">Phases:</span>
                  <span className="text-gray-600">{projectPlan.phases.length}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">Total Tasks:</span>
                  <span className="text-gray-600">{projectPlan.phases.reduce((acc, p) => acc + p.tasks.length, 0)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Key Features Alert */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-blue-600 flex-shrink-0 mt-1" size={20} />
            <div>
              <h3 className="font-bold text-blue-900 mb-2">Enhanced Features Beyond Zoho CRM:</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>✓ <strong>Multi-tenant architecture</strong> - Multiple legal entities with user access control</li>
                <li>✓ <strong>Unlimited territory management</strong> - Hierarchies, rules, pricing, workflows</li>
                <li>✓ <strong>Complete Quote-to-Cash</strong> - RFQ → Quote → Approval → Sales Order → Fulfillment</li>
                <li>✓ <strong>Vendor Management</strong> - Performance tracking, lifecycle, procurement workflows</li>
                <li>✓ <strong>Custom templates</strong> - Upload your own quote/SO templates</li>
                <li>✓ <strong>Advanced forecasting & DSO</strong> - Financial analytics and predictions</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Phases */}
        <div className="space-y-4">
          {projectPlan.phases.map((phase) => (
            <div 
              key={phase.id}
              className={`bg-white rounded-xl shadow-lg border-l-4 ${getPhaseColor(phase.priority)} overflow-hidden transition-all hover:shadow-xl`}
            >
              {/* Phase Header */}
              <div 
                className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => togglePhase(phase.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    {expandedPhases[phase.id] ? 
                      <ChevronDown className="text-gray-600 flex-shrink-0" size={24} /> : 
                      <ChevronRight className="text-gray-600 flex-shrink-0" size={24} />
                    }
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-xl font-bold text-gray-900">
                          Phase {phase.id}: {phase.name}
                        </h2>
                        <span className={`text-xs px-3 py-1 rounded-full font-semibold ${getPriorityBadge(phase.priority)}`}>
                          {phase.priority}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{phase.description}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>{phase.weeks}</span>
                        <span>•</span>
                        <span>{phase.duration}</span>
                        <span>•</span>
                        <span className="font-semibold text-blue-600">{phase.tasks.length} tasks</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tasks */}
              {expandedPhases[phase.id] && (
                <div className="px-6 pb-6 space-y-4 bg-gray-50">
                  {phase.tasks.map((task) => (
                    <div 
                      key={task.id}
                      className="bg-white rounded-lg p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start gap-3">
                        <button
                          onClick={() => toggleTask(task.id)}
                          className="mt-1 flex-shrink-0 hover:scale-110 transition-transform"
                        >
                          {completedTasks[task.id] ? 
                            <CheckCircle className="text-green-500" size={22} /> : 
                            <Circle className="text-gray-400" size={22} />
                          }
                        </button>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <h3 className={`font-bold text-gray-900 ${completedTasks[task.id] ? 'line-through text-gray-500' : ''}`}>
                              {task.id} - {task.name}
                            </h3>
                            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${getPriorityBadge(task.priority)}`}>
                              {task.priority}
                            </span>
                          </div>
                          <ul className="space-y-2">
                            {task.subtasks.map((subtask, idx) => (
                              <li 
                                key={idx}
                                className="text-sm text-gray-700 flex items-start gap-2 pl-2"
                              >
                                <span className="text-blue-500 font-bold mt-0.5">›</span>
                                <span>{subtask}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Timeline Summary */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-xl p-8 mt-8 text-white">
          <h3 className="text-2xl font-bold mb-4">Project Timeline Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <div className="text-3xl font-bold mb-1">3 months</div>
              <div className="text-sm opacity-90">Core CRM + Multi-tenant</div>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <div className="text-3xl font-bold mb-1">6 months</div>
              <div className="text-sm opacity-90">Full Quote-to-Cash System</div>
            </div>
            <div className="bg-white bg-opacity-20 rounded-lg p-4">
              <div className="text-3xl font-bold mb-1">12 months</div>
              <div className="text-sm opacity-90">Production-Ready Enterprise</div>
            </div>
          </div>
        </div>

        {/* Usage Instructions */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mt-6">
          <h3 className="font-bold text-amber-900 mb-3 text-lg">📋 How to Use This Plan:</h3>
          <ul className="text-sm text-amber-800 space-y-2">
            <li>• <strong>Click each phase</strong> to expand and see detailed tasks and subtasks</li>
            <li>• <strong>Check off tasks</strong> as you complete them to track progress</li>
            <li>• <strong>Follow the priority labels</strong> - Focus on Critical tasks first</li>
            <li>• <strong>Phases build on each other</strong> - Complete them in order</li>
            <li>• <strong>With 5-6 hours daily</strong>, expect 12-15 months for full production system</li>
            <li>• <strong>Can launch MVP</strong> after Phase 5 (Week 22) with basic CRM features</li>
            <li>• <strong>Adjust timeline</strong> based on your learning curve and team size</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default EnterpriseERPProjectPlan;