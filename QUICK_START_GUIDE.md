# 🚀 Quick Start Guide - Enhanced User Management

## 📋 Overview

This guide will help you get started with the enhanced user management system in the CRM application.

---

## 🛠️ Setup Instructions

### Backend Setup

#### 1. Install Dependencies
```bash
cd /path/to/Claude-CRM
pip install -r requirements.txt
```

#### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 3. Create Initial Data (Optional)
```python
# Create sample permissions
python manage.py shell

from core.models import Permission, Role, Company

# Create permissions
permissions = [
    {'name': 'View Contacts', 'codename': 'view_contact', 'module': 'Contacts'},
    {'name': 'Create Contacts', 'codename': 'create_contact', 'module': 'Contacts'},
    {'name': 'Edit Contacts', 'codename': 'edit_contact', 'module': 'Contacts'},
    {'name': 'Delete Contacts', 'codename': 'delete_contact', 'module': 'Contacts'},
]

for perm_data in permissions:
    Permission.objects.get_or_create(**perm_data)
```

#### 4. Start Development Server
```bash
python manage.py runserver
```

The backend will be available at `http://localhost:8000/`

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Configure Environment
Create `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000/api
```

#### 3. Start Development Server
```bash
npm start
```

The frontend will be available at `http://localhost:3000/`

---

## 🔐 API Endpoints

### User Management

#### List Users
```bash
GET /api/core/users/
Query Parameters:
  - page: int (page number)
  - page_size: int (items per page)
  - search: string (search term)
  - is_active: boolean (filter by status)
```

#### Get User Statistics
```bash
GET /api/core/users/statistics/
Response:
{
  "total_users": 15,
  "active_users": 12,
  "inactive_users": 1,
  "pending_invitations": 2,
  "users_by_role": {"admin": 3, "manager": 5},
  "recent_activities": [...]
}
```

#### Create User
```bash
POST /api/core/users/
Body:
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true
}
```

#### Bulk User Action
```bash
POST /api/core/users/bulk_action/
Body:
{
  "user_ids": ["uuid1", "uuid2"],
  "action": "activate"  // or "deactivate", "delete"
}
```

#### Get User Activities
```bash
GET /api/core/users/{user_id}/activities/
Response:
[
  {
    "id": "uuid",
    "activity_type": "login",
    "module": "Authentication",
    "description": "User logged in",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Role Management

#### List Roles
```bash
GET /api/core/roles/
```

#### Create Role
```bash
POST /api/core/roles/
Body:
{
  "name": "Sales Manager",
  "description": "Manages sales team",
  "company": "company_uuid"
}
```

#### Assign Permissions to Role
```bash
POST /api/core/roles/{role_id}/assign_permissions/
Body:
{
  "permission_ids": ["perm_uuid1", "perm_uuid2"]
}
```

### User Invitations

#### Create Invitation
```bash
POST /api/core/user-invitations/
Body:
{
  "email": "newuser@example.com",
  "role": "role_uuid",
  "message": "Welcome to our team!"
}
```

#### Resend Invitation
```bash
POST /api/core/user-invitations/{invitation_id}/resend/
```

---

## 💻 Frontend Usage

### Using the API Service

```javascript
import userManagementService from './services/userManagementService';

// Fetch users
const fetchUsers = async () => {
  try {
    const users = await userManagementService.getUsers({
      page: 1,
      page_size: 10,
      search: 'john'
    });
    console.log(users);
  } catch (error) {
    console.error('Error fetching users:', error);
  }
};

// Create user
const createUser = async (userData) => {
  try {
    const newUser = await userManagementService.createUser(userData);
    console.log('User created:', newUser);
  } catch (error) {
    console.error('Error creating user:', error);
  }
};

// Bulk action
const deactivateUsers = async (userIds) => {
  try {
    await userManagementService.bulkUserAction(userIds, 'deactivate');
    console.log('Users deactivated');
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Using Components

#### User Management
```jsx
import UserManagement from './pages/Settings/UserManagement';

function App() {
  return (
    <div>
      <UserManagement />
    </div>
  );
}
```

#### Role Management
```jsx
import RoleManagement from './pages/Settings/RoleManagement';

function App() {
  return (
    <div>
      <RoleManagement />
    </div>
  );
}
```

#### Admin Panel (All in One)
```jsx
import AdminPanel from './pages/Settings/AdminPanel';

function App() {
  return (
    <div>
      <AdminPanel />
    </div>
  );
}
```

---

## 🔧 Common Tasks

### Adding a New Permission

```python
from core.models import Permission

permission = Permission.objects.create(
    name='Export Reports',
    codename='export_reports',
    module='Reports',
    description='Allow exporting reports to various formats'
)
```

### Creating a Role with Permissions

```python
from core.models import Role, Permission, Company

company = Company.objects.first()
role = Role.objects.create(
    name='Report Viewer',
    description='Can view and export reports',
    company=company
)

# Assign permissions
report_perms = Permission.objects.filter(module='Reports')
role.permissions.set(report_perms)
```

### Assigning Role to User

```python
from core.models import UserRole, User, Role
from django.utils import timezone
from datetime import timedelta

user = User.objects.get(email='user@example.com')
role = Role.objects.get(name='Report Viewer')

user_role = UserRole.objects.create(
    user=user,
    role=role,
    assigned_by=admin_user,
    expires_at=timezone.now() + timedelta(days=365)
)
```

### Tracking User Activity

```python
from core.models import UserActivity

activity = UserActivity.objects.create(
    user=request.user,
    activity_type='create',
    module='Contacts',
    description='Created new contact',
    ip_address=request.META.get('REMOTE_ADDR'),
    metadata={'contact_id': str(contact.id)}
)
```

### Creating User Invitation

```python
from core.models import UserInvitation
from datetime import timedelta

invitation = UserInvitation.objects.create(
    email='newuser@example.com',
    company=company,
    invited_by=request.user,
    role=role,
    expires_at=timezone.now() + timedelta(days=7),
    message='Welcome to our CRM!'
)
```

---

## 🧪 Testing

### Backend Tests

```python
# tests/test_user_management.py
from django.test import TestCase
from core.models import User, Role, Permission

class UserManagementTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
    
    def test_assign_role(self):
        # Add test implementation
        pass
```

Run tests:
```bash
python manage.py test core.tests
```

### Frontend Tests

```javascript
// UserManagement.test.jsx
import { render, screen } from '@testing-library/react';
import UserManagement from './UserManagement';

test('renders user management component', () => {
  render(<UserManagement />);
  const heading = screen.getByText(/User Management/i);
  expect(heading).toBeInTheDocument();
});
```

Run tests:
```bash
npm test
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Migration Errors
```bash
# Reset migrations (development only!)
python manage.py migrate core zero
python manage.py migrate
```

#### 2. Frontend Not Connecting to Backend
- Check CORS settings in Django
- Verify `REACT_APP_API_URL` in frontend `.env`
- Check Django `ALLOWED_HOSTS` setting

#### 3. Permission Denied Errors
- Verify user authentication
- Check user role assignments
- Validate permission assignments to roles

---

## 📚 Additional Resources

### Documentation
- [USER_MANAGEMENT_ENHANCEMENTS.md](./USER_MANAGEMENT_ENHANCEMENTS.md) - Detailed features
- [CRM_GAP_ANALYSIS_IMPLEMENTATION.md](./CRM_GAP_ANALYSIS_IMPLEMENTATION.md) - Implementation summary
- [UI_UX_ENHANCEMENTS_VISUAL_GUIDE.md](./UI_UX_ENHANCEMENTS_VISUAL_GUIDE.md) - Visual guide

### API Documentation
- Django REST Framework browsable API: `http://localhost:8000/api/`
- Swagger documentation: `http://localhost:8000/api/docs/` (if configured)

### Support
- Create an issue on GitHub
- Check existing documentation
- Review code comments

---

## ✅ Checklist

Before deploying:
- [ ] Run all migrations
- [ ] Create initial permissions and roles
- [ ] Test API endpoints
- [ ] Verify frontend connectivity
- [ ] Check user authentication
- [ ] Test role-based access
- [ ] Verify activity logging
- [ ] Test invitation system
- [ ] Check responsive design
- [ ] Validate error handling

---

## 🎉 You're Ready!

You now have a fully functional enhanced user management system. Start by:
1. Creating your first role
2. Adding permissions to the role
3. Creating users
4. Assigning roles to users
5. Testing the interface

Happy coding! 🚀
