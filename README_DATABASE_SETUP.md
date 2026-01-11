# Database Setup Instructions

**Important:** Add these steps to the README.md Installation section after "Install dependencies"

## Database Migration (Phase 3+)

After installing dependencies, you must run database migrations to create the required tables:

```bash
# Navigate to backend directory
cd backend

# Run migrations to create database schema
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> c2a0d09f419f, Add knowledge graph tables
```

**Note:** The application will NOT create tables automatically. You must run migrations explicitly using Alembic.

### Verify Tables

You can verify the tables were created:

```bash
docker exec -it insightgraph-postgres psql -U dev -d insightgraph -c "\dt"
```

You should see:
```
          List of relations
 Schema |  Name  | Type  |  Owner
--------+--------+-------+--------
 public | edges  | table | dev
 public | graphs | table | dev
 public | nodes  | table | dev
```

### Troubleshooting

If you see "Tables not found" warning on startup:
```
[Database] WARNING: Tables not found. Run 'alembic upgrade head' to create schema.
```

This means you forgot to run migrations. Simply run:
```bash
cd backend
alembic upgrade head
```

Then restart the server.
