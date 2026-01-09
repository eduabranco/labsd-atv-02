# Setup Flow Diagram

## New Setup Process (Automated)

```
┌─────────────────────────────────────────────────────────────┐
│                    START: New Installation                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ pip install -r       │
                  │ requirements.txt     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ python3 db_setup.py  │◄──── AUTOMATED!
                  └──────────┬───────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌────────────────┐           ┌────────────────┐
     │ Auto-detect    │           │ Manual         │
     │ MySQL:         │           │ Configuration  │
     │ - No password  │           │ (if needed)    │
     │ - 'password'   │           │                │
     │ - root/custom  │           │                │
     └────────┬───────┘           └────────┬───────┘
              │                             │
              └──────────────┬──────────────┘
                             ▼
                  ┌──────────────────────┐
                  │ Create:              │
                  │ - Database dist_db   │
                  │ - Table usuarios     │
                  │ - User (optional)    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Generate:            │
                  │ config_db.py         │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ python3              │
                  │ verify_setup.py      │◄──── VERIFY!
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Update config.py     │
                  │ with Node IPs        │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ python middleware.py │
                  │ <NODE_ID>            │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ python client.py     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   SYSTEM RUNNING! 🎉  │
                  └──────────────────────┘
```

## Configuration Priority Flow

```
┌─────────────────────────────────────────┐
│  Application Starts (middleware.py)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Load config.py       │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ get_db_config()      │
        └──────────┬───────────┘
                   │
      ┌────────────┴────────────┐
      ▼                         │
┌──────────────┐                │
│ Try import   │                │
│ config_db.py │                │
└──────┬───────┘                │
       │                        │
  ┌────┴─────┐                  │
  ▼          ▼                  │
SUCCESS    FAIL                 │
  │          │                  │
  │          └──────────────────┤
  │                             ▼
  │                  ┌──────────────────┐
  │                  │ Check ENV vars:  │
  │                  │ - MYSQL_USER     │
  │                  │ - MYSQL_PASSWORD │
  │                  │ - MYSQL_HOST     │
  │                  │ - MYSQL_DATABASE │
  │                  └──────┬───────────┘
  │                         │
  │                    ┌────┴─────┐
  │                    ▼          ▼
  │                  FOUND     NOT FOUND
  │                    │          │
  │                    │          ▼
  │                    │   ┌──────────────┐
  │                    │   │ Use defaults │
  │                    │   │ (root/no pwd)│
  │                    │   └──────┬───────┘
  │                    │          │
  └────────────────────┴──────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ DB_CONFIG available  │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ Connect to MySQL     │
            └──────────────────────┘
```

## Multi-Node Deployment Flow

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Machine 1  │  │  Machine 2  │  │  Machine 3  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Install     │  │ Install     │  │ Install     │
│ dependencies│  │ dependencies│  │ dependencies│
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ db_setup.py │  │ db_setup.py │  │ db_setup.py │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Update      │  │ Update      │  │ Update      │
│ config.py   │  │ config.py   │  │ config.py   │
│ NODES dict  │  │ NODES dict  │  │ NODES dict  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ python      │  │ python      │  │ python      │
│ middleware  │  │ middleware  │  │ middleware  │
│ .py 1       │  │ .py 2       │  │ .py 3       │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ Heartbeat &   │
                │ Leader Election│
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │ Node 3 becomes│
                │ Leader (max ID)│
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │ Ready for     │
                │ client queries│
                └───────────────┘
```

## Authentication Methods Supported

```
MySQL Authentication
        │
        ├─► Root (no password)
        │   └─► Auto-detected ✓
        │
        ├─► Root (password = 'password')
        │   └─► Auto-detected ✓
        │
        ├─► Root (custom password)
        │   └─► Manual/ENV vars ✓
        │
        ├─► Custom User (created by db_setup.py)
        │   └─► Auto-configured ✓
        │
        └─► Custom User (existing)
            └─► Manual/ENV vars ✓
```

## File Dependencies

```
middleware.py
    │
    ├─► config.py
    │   │
    │   ├─► config_db.py (generated)  [PRIORITY 1]
    │   │   └─► Created by db_setup.py
    │   │
    │   ├─► Environment Variables     [PRIORITY 2]
    │   │   └─► .env or export
    │   │
    │   └─► Defaults                  [PRIORITY 3]
    │       └─► root with no password
    │
    └─► mysql.connector
        └─► Connects to MySQL

client.py
    └─► config.py (for NODES only)

db_setup.py (run once per node)
    ├─► Detects MySQL credentials
    ├─► Creates database & table
    ├─► Optionally creates user
    └─► Generates config_db.py

verify_setup.py (optional check)
    ├─► Checks dependencies
    ├─► Tests DB connection
    └─► Validates configuration
```
