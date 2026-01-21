# database-ops.md Template

<!-- SCOPE: database-ops.md command template ONLY. Contains migration/backup/reset steps, conditional generation. -->
<!-- DO NOT add here: Generation workflow → ln-751-command-templates SKILL.md -->

Template for generating database operations command.

**Condition:** Generated only if database detected (PostgreSQL in docker-compose, EF Core, etc.)

---

## Generated Command

```markdown
---
description: Database operations - migrations, backup, reset
allowed-tools: Bash, Read
---

# Database Operations ({{PROJECT_NAME}})

Common database tasks for development and maintenance.

---

## Migrations

### Apply Pending Migrations
```bash
cd {{BACKEND_ROOT}}
dotnet ef database update
```

### Create New Migration
```bash
dotnet ef migrations add MigrationName --project {{BACKEND_ROOT}}
```

### List Migrations
```bash
dotnet ef migrations list --project {{BACKEND_ROOT}}
```

### Rollback to Specific Migration
```bash
dotnet ef database update PreviousMigrationName --project {{BACKEND_ROOT}}
```

### Generate SQL Script
```bash
dotnet ef migrations script --project {{BACKEND_ROOT}} -o migration.sql
```

---

## Database Reset

### Full Reset (Development Only)
```bash
# Stop services
docker-compose down

# Remove database volume
docker-compose down -v

# Restart with fresh database
docker-compose up -d postgres
sleep 5

# Apply all migrations
cd {{BACKEND_ROOT}} && dotnet ef database update
```

### Drop and Recreate
```bash
dotnet ef database drop --force --project {{BACKEND_ROOT}}
dotnet ef database update --project {{BACKEND_ROOT}}
```

---

## Backup & Restore

### Backup PostgreSQL
```bash
docker-compose exec postgres pg_dump -U postgres {{PROJECT_NAME}} > backup_$(date +%Y%m%d).sql
```

### Restore PostgreSQL
```bash
docker-compose exec -T postgres psql -U postgres {{PROJECT_NAME}} < backup_20260110.sql
```

### Backup with Compression
```bash
docker-compose exec postgres pg_dump -U postgres {{PROJECT_NAME}} | gzip > backup_$(date +%Y%m%d).sql.gz
```

---

## Database Shell

### Connect to PostgreSQL
```bash
docker-compose exec postgres psql -U postgres {{PROJECT_NAME}}
```

### Common SQL Commands
```sql
-- List tables
\dt

-- Describe table
\d table_name

-- Show table contents
SELECT * FROM table_name LIMIT 10;

-- Exit
\q
```

---

## Troubleshooting

### Check Database Status
```bash
docker-compose exec postgres pg_isready
```

### View Database Logs
```bash
docker-compose logs -f postgres
```

### Check Connection String
```bash
# From appsettings.json or .env
cat {{BACKEND_ROOT}}/appsettings.Development.json | grep -A5 ConnectionStrings
```

### Reset EF Tools Cache
```bash
dotnet tool restore
```

---

## Seed Data

### Run Seed (if configured)
```bash
cd {{BACKEND_ROOT}}
dotnet run -- seed
```

### Manual Seed SQL
```bash
docker-compose exec -T postgres psql -U postgres {{PROJECT_NAME}} < seed.sql
```

---

**Generated:** {{TIMESTAMP}}
```

---

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PROJECT_NAME}}` | Project name / database name | "kehai-os" |
| `{{BACKEND_ROOT}}` | Backend path | "src/Kehai.Api" |
| `{{TIMESTAMP}}` | Generation time | "2026-01-10" |

---

**Version:** 2.0.0
**Last Updated:** 2026-01-10
