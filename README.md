# DormMate — Smart Shared Dormitory Resource & Task Management System

![DormMate Banner](https://github.com/user-attachments/assets/0aa3270a-e428-4613-a9b1-b67af38e2917)

> **COMP2116 Software Engineering — Final Project**  
> Macao Polytechnic University, 2025/26 Semester 2

---

## 📌 Graphical Abstract

![Graphical Abstract](https://github.com/user-attachments/assets/453b8852-f93f-48c9-8fb8-6bd1216468cf)



DormMate is a **web-based smart dormitory management system** designed for university students sharing dormitory rooms. It solves the common pain points of shared living — scheduling shared resources (washing machines, kitchens), rotating chores fairly, splitting expenses transparently, and keeping roommates informed through a notice board — all in one unified platform built with **Django** and **Bootstrap 5**.

---

## 🎯 Purpose of the Software

### Problem Statement

University dormitory life involves constant coordination among roommates: **who uses the washing machine when, whose turn it is to clean, how to split the electricity bill, and how to communicate important notices.** Currently, most students rely on scattered WeChat messages, verbal agreements, and memory — leading to conflicts, forgotten duties, and unfair expense splits.

**DormMate** solves this by providing a centralized digital platform for all dormitory coordination needs.

### Software Development Process

We adopted the **Agile (Scrum)** software development process for this project.

#### Why Agile Instead of Waterfall?

| Factor | Waterfall | Agile (Our Choice) |
|--------|-----------|---------------------|
| **Requirements** | Must be fully defined upfront | Can evolve iteratively — we discovered new features during development |
| **Timeline** | Sequential phases take longer | Parallel development with sprints — ideal for our 4-week window |
| **Adaptability** | Rigid; costly to change | Flexible; we pivoted from "booking only" to adding chores and expenses mid-project |
| **Team Dynamics** | Clear handoff between roles | Collaborative; our small team needed overlap and communication |
| **Delivery** | Single final delivery | Incremental deliveries every sprint — we had working software from Sprint 1 |
| **Risk** | Late discovery of integration issues | Early and continuous integration reduces risk |

**Conclusion:** With a 3-person team, a 4-week timeline, and evolving feature scope, Agile was the natural choice. Waterfall would have been too rigid — for example, the expense splitting feature was added in Sprint 2 after we realized its importance through user feedback from our roommates.

### Target Market & Possible Usage

1. **University Dormitory Students** (primary) — Managing day-to-day shared living in 2–6 person dorm rooms
2. **Shared Apartment Tenants** — Young professionals sharing apartments who need resource scheduling and expense splitting
3. **Student Housing Administrators** — Deploying across an entire dormitory building for standardized management
4. **Co-living Spaces** — Modern co-living operators can use DormMate as a lightweight tenant coordination tool

**Competitive Advantage:** Unlike generic task management tools (Trello, Notion) or expense-splitting apps (Splitwise), DormMate is **purpose-built for shared living** — combining resource booking, chore rotation, expense splitting, and announcements in a single cohesive platform. It is also self-hosted and free.

---

## 🛠 Software Development Plan

### Development Process

We used **Scrum** with the following practices:

- **Sprint Length:** 2 weeks
- **Sprint Planning:** Select user stories from backlog at the start of each sprint
- **Daily Stand-ups:** Async updates via WeChat group + GitHub Issues tracking
- **Sprint Review:** Demo of working features to each other at end of sprint
- **Sprint Retrospective:** Brief reflection on process improvement
- **Version Control:** GitHub with feature branch workflow (feature branches → `main` via pull requests)

### Members — Roles, Responsibilities & Contribution

| Member | Student ID | Role | Responsibilities | Contribution |
|--------|-----------|------|-----------------|-------------|
| **Ouyang Yuzhi** | P2421170 | **Project Manager & Frontend Developer** | Sprint planning, task tracking, UI/UX design, all HTML/CSS templates, Bootstrap integration, responsive design, user experience testing | 35% |
| **Xiaoboming** | P2421718 | **Backend Developer & Database Architect** | Django models & migrations, views & URL routing, business logic (booking conflict detection, expense splitting algorithm, chore rotation algorithm), user authentication, forms & validation | 35% |
| **Xie Zhenyun** | P2421511 | **QA Engineer & DevOps** | Unit & integration testing (15 test cases), bug fixing, deployment configuration, README documentation, demo video recording & editing, code review | 30% |

### Schedule

| Sprint | Duration | Milestones | Key Deliverables |
|--------|----------|-----------|-----------------|
| **Sprint 0** | Mar 24 – Mar 30 | Project inception | Idea selection, technology stack decision, GitHub repo setup, initial Django project skeleton |
| **Sprint 1** | Mar 31 – Apr 6 | Core infrastructure | User registration/login/logout, Room create/join with invite code system, Dashboard layout, base template with sidebar navigation |
| **Sprint 2** | Apr 7 – Apr 13 | Feature development | Resource CRUD + booking system with conflict detection, Chore management + auto-rotation algorithm, Expense tracking + per-person splitting + balance calculation, Announcement board |
| **Sprint 3** | Apr 14 – Apr 19 | Polish & delivery | Analytics dashboard, context processor for global room state, UI refinements, unit testing (15 tests), README documentation, demo video production |

### Algorithm

DormMate implements several non-trivial algorithms:

#### 1. Booking Conflict Detection Algorithm

When a user books a shared resource, the system checks for time overlaps with existing bookings:

```
Algorithm: BookingConflictDetection
Input: New booking B_new (resource, date, start_time, end_time)
Output: Boolean (has_conflict)

1. Query all ACTIVE bookings for the same resource on the same date:
   existing = Booking.filter(resource=B_new.resource, date=B_new.date, status='ACTIVE')

2. For each existing booking B_exist in existing:
   IF B_exist.start_time < B_new.end_time AND B_exist.end_time > B_new.start_time:
       RETURN True  (conflict detected — time ranges overlap)

3. RETURN False  (no conflict — slot is available)
```

**Implementation** (in `views.py`):
```python
conflicts = Booking.objects.filter(
    resource=resource, date=booking.date, status='ACTIVE'
).filter(
    Q(start_time__lt=booking.end_time, end_time__gt=booking.start_time)
)
```

This uses the classic interval overlap condition: two intervals [a, b) and [c, d) overlap if and only if `a < d AND c < b`.

#### 2. Chore Auto-Rotation Algorithm (Round-Robin)

Automatically assigns chores to members in a fair rotating manner:

```
Algorithm: ChoreAutoRotation
Input: Room R with members M[], chores C[]
Output: New ChoreAssignment records

1. members = list(R.members)
2. chores = list(R.chores)
3. today = current_date()

4. FOR i = 0 TO len(chores) - 1:
   a. chore = chores[i]
   b. IF chore already has a pending assignment with due_date >= today:
        SKIP (avoid duplicate assignment)
   c. member_index = i MOD len(members)     // Round-robin selection
   d. assigned_member = members[member_index]
   e. frequency_days = {DAILY:1, WEEKLY:7, BIWEEKLY:14, MONTHLY:30}
   f. due_date = today + frequency_days[chore.frequency]
   g. CREATE ChoreAssignment(chore, assigned_member, due_date)

5. RETURN count of created assignments
```

The **round-robin** approach ensures each member gets an approximately equal number of chores. The modulo operation distributes chores cyclically across all members.

#### 3. Expense Per-Person Splitting Algorithm

```
Algorithm: ExpensePerPersonSplit
Input: Expense E with amount A, split_among set S
Output: Per-person amount (rounded up to avoid shortfall)

1. count = |S|  (number of people sharing the expense)
2. IF count == 0: RETURN A  (edge case: no split members)
3. raw_split = A / count
4. per_person = CEIL(raw_split * 100) / 100  (round UP to 2 decimal places)
5. RETURN per_person
```

**Why round up?** When splitting MOP 100.00 among 3 people, a naive division gives 33.333... We round **up** to MOP 33.34 so the payer is never shortchanged. The slight overpayment (MOP 0.02 total) is negligible and prevents persistent debt.

#### 4. Balance Calculation Algorithm

```
Algorithm: BalanceCalculation
Input: Room R with unsettled expenses E[]
Output: Net balance per member

1. FOR each member M in R.members:
   a. paid = SUM(E.amount WHERE E.paid_by == M AND E.is_settled == False)
   b. owed = SUM(E.per_person_amount WHERE M IN E.split_among AND E.is_settled == False)
   c. net_balance[M] = paid - owed

2. RETURN net_balance
   // Positive = others owe you money
   // Negative = you owe others money
```

#### 5. Overdue Detection (applied to Chore Assignments)

```
Algorithm: OverdueDetection
Input: ChoreAssignment A
Output: Boolean

1. IF A.status != 'PENDING': RETURN False
2. IF A.due_date < current_date(): RETURN True
3. RETURN False
```

### Current Status

| Module | Features | Status |
|--------|----------|--------|
| **Authentication** | Register, Login, Logout | ✅ Complete |
| **Room Management** | Create room, join via invite code, edit room, member list | ✅ Complete |
| **Resource Booking** | Add shared resources, 7-day calendar view, time-slot booking with conflict detection, cancel bookings | ✅ Complete |
| **Chore System** | Create chore types, manual assignment, auto-rotation (round-robin), mark complete, overdue detection | ✅ Complete |
| **Expense Splitting** | Add expenses, auto-split among all members, per-person calculation, balance overview, settle expenses | ✅ Complete |
| **Announcements** | Post/delete announcements, priority levels (Info/Warning/Urgent), pin important notices | ✅ Complete |
| **Analytics** | Chore completion rate per member, expense contribution per member, resource usage by category, expense breakdown by category | ✅ Complete |
| **Activity Log** | Full audit trail of all actions (create, book, cancel, complete, join) | ✅ Complete |
| **UI/UX** | Responsive sidebar navigation, mobile-friendly, clean dashboard with stats cards | ✅ Complete |
| **Admin Panel** | Django admin for all models with filters and search | ✅ Complete |
| **Testing** | 15 unit & integration tests covering models and views | ✅ Complete |
| **Drag-and-Drop** | Drag tasks between status columns | ⏳ Future |
| **Push Notifications** | Browser push notifications for bookings and chore reminders | ⏳ Future |
| **Custom Split Ratios** | Allow unequal expense splitting (e.g., 60/40) | ⏳ Future |
| **REST API** | RESTful API for mobile app integration | ⏳ Future |

**Overall Status:** The software is at **pilot/demo stage** — fully functional for all core dormitory management workflows with a polished, professional interface.

### Future Plan

1. **Drag-and-Drop Booking** — Visual drag-and-drop on the resource calendar using FullCalendar.js
2. **Push Notifications** — Browser notifications for upcoming bookings and overdue chores
3. **Custom Expense Split** — Allow weighted or custom split ratios instead of always equal split
4. **REST API** — Django REST Framework API for building a companion mobile app (Flutter/React Native)
5. **WeChat Mini Program** — Integration with WeChat for notifications and quick actions
6. **Room Templates** — Pre-configured resource and chore templates for common dormitory setups
7. **Cloud Deployment** — Deploy on PythonAnywhere or Alibaba Cloud for production use

---

## 🎬 Demo

📺 **Demo Video:** [YouTube Link](https://youtu.be/YOUR_VIDEO_ID_HERE)

<!-- TODO: Replace with actual YouTube URL after recording -->

The demo video covers:
1. How to install and start the software (pip install, migrate, runserver)
2. User registration and login
3. Creating a dormitory room and sharing the invite code
4. Another user joining the room via invite code
5. Adding shared resources (washing machine, kitchen) and booking time slots
6. Creating chores and using auto-rotation to assign them fairly
7. Adding shared expenses and viewing the balance overview
8. Posting announcements to the notice board
9. Viewing analytics dashboard

**Duration:** ~12 minutes

---

## 💻 Development & Running Environment

### Programming Language
- **Python 3.10+** (backend logic, ORM, business rules)
- **HTML5 / CSS3 / JavaScript** (frontend templates)

### Framework & Libraries
- **Django 4.2** — Full-stack web framework (models, views, templates, ORM, auth)
- **Bootstrap 5.3** — Responsive CSS framework (CDN)
- **Bootstrap Icons 1.10** — Icon library (CDN)
- **Plus Jakarta Sans** — Typography via Google Fonts (CDN)
- **SQLite 3** — Lightweight relational database (built into Python)

### Minimum Hardware Requirements
- **CPU:** Any modern processor (x86_64 or ARM)
- **RAM:** 512 MB minimum, 1 GB recommended
- **Disk:** 100 MB free space

### Minimum Software Requirements
- **OS:** Windows 10+, macOS 10.15+, Ubuntu 20.04+, or any Linux distribution
- **Python:** 3.10 or higher
- **pip:** Python package manager (bundled with Python)
- **Web Browser:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### Required Packages
```
Django>=4.2,<5.0
```
No additional packages needed — DormMate runs on Django alone with CDN-hosted frontend dependencies.

### Installation & Running

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/DormMate.git
cd DormMate

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
# or
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create admin superuser (optional, for Django admin panel)
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver

# 7. Open browser and go to:
# http://127.0.0.1:8000/
```

### Quick Start Guide

1. **Register** an account at `/register/`
2. **Create a Room** — give it a name (e.g., "Room 301-A"), building, floor, capacity
3. **Share the Invite Code** with your roommates so they can join
4. **Add Shared Resources** — e.g., "Washing Machine #1", "Kitchen Stove"
5. **Book Resources** — select a date and time slot
6. **Set Up Chores** — create recurring chores like "Clean Bathroom", "Take Out Trash"
7. **Use Auto-Rotate** to fairly distribute chores among members
8. **Log Expenses** — track shared costs like utilities and supplies
9. **Post Announcements** — keep everyone informed

---

## 📜 Declaration

### Open Source Libraries Used

| Library | Version | License | Purpose | Modified? |
|---------|---------|---------|---------|-----------|
| [Django](https://www.djangoproject.com/) | 4.2 | BSD-3-Clause | Web application framework | No |
| [Bootstrap](https://getbootstrap.com/) | 5.3.0 | MIT | Frontend CSS framework (via CDN) | No |
| [Bootstrap Icons](https://icons.getbootstrap.com/) | 1.10.0 | MIT | Icon library (via CDN) | No |
| [Google Fonts — Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans) | — | OFL | Web typography (via CDN) | No |

### Original Work Declaration

All source code in this repository — including all Python/Django backend code (models, views, forms, URLs, tests, context processors), all HTML templates, and all CSS styling — is **original work** developed by our team members. No code was copied from other projects or repositories.

The open source libraries listed above are used as **external dependencies** via `pip install` (Django) or CDN links (Bootstrap, fonts, icons) and were **not** modified or vendored into our codebase.

---

## 📁 Project Structure

```
DormMate/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── README.md                    # This documentation
│
├── dormmate/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py              # Project settings (DB, apps, timezone, etc.)
│   ├── urls.py                  # Root URL configuration
│   └── wsgi.py                  # WSGI entry point for deployment
│
├── dorm/                        # Main application
│   ├── __init__.py
│   ├── admin.py                 # Admin panel configuration (8 model admins)
│   ├── apps.py                  # App configuration
│   ├── context_processors.py    # Global template context (current room)
│   ├── forms.py                 # 9 form definitions
│   ├── models.py                # 8 database models
│   ├── tests.py                 # 15 unit & integration tests
│   ├── urls.py                  # 22 URL patterns
│   └── views.py                 # 20 view functions
│
├── templates/                   # HTML templates (16 files)
│   ├── base.html                # Base layout with sidebar & top bar
│   ├── registration/
│   │   ├── login.html           # Login page
│   │   └── register.html        # Registration page
│   └── dorm/
│       ├── dashboard.html       # Main dashboard with stats & activity
│       ├── room_form.html       # Create / edit room
│       ├── room_join.html       # Join room via invite code
│       ├── room_detail.html     # Room overview with members & resources
│       ├── resource_form.html   # Add shared resource
│       ├── resource_schedule.html # Resource booking calendar
│       ├── booking_form.html    # Book a time slot
│       ├── chore_list.html      # Chore schedule (pending + completed)
│       ├── chore_form.html      # Create chore type
│       ├── chore_assign_form.html # Manually assign chore
│       ├── expense_list.html    # Expense list with balance overview
│       ├── expense_form.html    # Add shared expense
│       ├── announcement_list.html # Announcement board
│       ├── announcement_form.html # Post announcement
│       └── analytics.html       # Room analytics dashboard
│
└── static/                      # Static assets (CSS, JS, images)
    ├── css/
    ├── js/
    └── images/
```

---

## 📊 Database Schema (ER Diagram)

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────────┐
│     User     │         │       Room       │         │    Resource      │
├──────────────┤         ├──────────────────┤         ├──────────────────┤
│ id (PK)      │────┐    │ id (PK)          │────┐    │ id (PK)          │
│ username     │    │    │ name             │    │    │ name             │
│ email        │    ├──▶│ building         │    ├──▶│ category         │
│ first_name   │    │    │ floor            │    │    │ room_id (FK)     │
│ last_name    │    │    │ capacity         │    │    │ slot_duration    │
│ password     │    │    │ owner_id (FK)    │    │    │ available_from   │
└──────────────┘    │    │ invite_code      │    │    │ available_until  │
                    │    │ members (M2M)    │    │    └──────────────────┘
                    │    └──────────────────┘    │             │
                    │                            │             ▼
┌──────────────────┐│    ┌──────────────────┐    │    ┌──────────────────┐
│   Announcement   ││    │      Chore       │    │    │     Booking      │
├──────────────────┤│    ├──────────────────┤    │    ├──────────────────┤
│ id (PK)          ││    │ id (PK)          │    │    │ id (PK)          │
│ title            ││    │ name             │    │    │ resource_id (FK) │
│ content          ││    │ description      │    │    │ user_id (FK)     │
│ room_id (FK)     │◀┤    │ room_id (FK)     │◀───┤    │ date             │
│ author_id (FK)   │ │    │ frequency        │    │    │ start_time       │
│ priority         │ │    └──────────────────┘    │    │ end_time         │
│ is_pinned        │ │             │              │    │ status           │
└──────────────────┘ │             ▼              │    └──────────────────┘
                     │    ┌──────────────────┐    │
┌──────────────────┐ │    │ ChoreAssignment  │    │    ┌──────────────────┐
│  ActivityLog     │ │    ├──────────────────┤    │    │     Expense      │
├──────────────────┤ │    │ id (PK)          │    │    ├──────────────────┤
│ id (PK)          │ │    │ chore_id (FK)    │    │    │ id (PK)          │
│ user_id (FK)     │◀┘    │ assigned_to (FK) │    └──▶│ title            │
│ action           │      │ due_date         │         │ amount           │
│ target_type      │      │ status           │         │ category         │
│ target_name      │      │ completed_at     │         │ paid_by (FK)     │
│ room_id (FK)     │      └──────────────────┘         │ room_id (FK)     │
│ timestamp        │                                   │ split_among (M2M)│
└──────────────────┘                                   │ is_settled       │
                                                       └──────────────────┘
```

**Key Relationships:**
- A **User** can own multiple Rooms and be a member of multiple Rooms (M2M)
- A **Room** contains Resources, Chores, Expenses, and Announcements
- A **Resource** has multiple Bookings (one-to-many)
- A **Chore** has multiple ChoreAssignments (one-to-many)
- An **Expense** is split among multiple Users (M2M via `split_among`)

---

## 🧪 Running Tests

```bash
python manage.py test dorm
```

**Test Suite (15 tests):**

| Category | Test | Description |
|----------|------|-------------|
| Room Model | `test_room_creation` | Verify room string representation and invite code generation |
| Room Model | `test_member_count` | Verify member counting |
| Room Model | `test_is_full` | Verify room capacity enforcement |
| Booking Model | `test_booking_creation` | Verify default booking status is ACTIVE |
| Booking Model | `test_past_booking` | Verify past booking detection |
| Chore Assignment | `test_overdue_detection` | Verify overdue chore detection |
| Chore Assignment | `test_not_overdue_when_done` | Verify completed chores are not marked overdue |
| Chore Assignment | `test_completed_at_auto_set` | Verify auto-timestamp when marking done |
| Expense Model | `test_per_person_amount` | Verify equal expense splitting |
| Expense Model | `test_per_person_odd_split` | Verify rounding behavior for non-divisible amounts |
| Views | `test_dashboard_requires_login` | Verify unauthenticated redirect |
| Views | `test_dashboard_authenticated` | Verify authenticated access |
| Views | `test_register_view` | Verify registration page loads |
| Views | `test_room_create` | Verify room creation via POST |
| Views | `test_room_join_with_code` | Verify invite code join mechanism |
| Views | `test_booking_conflict_detection` | Verify overlapping booking rejection |

---

## 👥 Team

| Name | Student ID | GitHub |
|------|-----------|--------|
| Ouyang Yuzhi | P2421170 | [@ouyangyuzhi](https://github.com/ouyangyuzhi) |
| Xiaoboming | P2421718 | [@xiaoboming](https://github.com/xiaoboming) |
| Xie Zhenyun | P2421511 | [@xiezhenyun](https://github.com/xiezhenyun) |

---

*COMP2116: Software Engineering — Macao Polytechnic University — 2025/26 Semester 2*
