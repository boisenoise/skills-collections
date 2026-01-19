# Drizzle Schema Parsing Patterns

Rules for parsing Drizzle ORM schemas and extracting entity information.

---

## Schema File Structure

| Element | Pattern | Purpose |
|---------|---------|---------|
| Table definition | `export const tableName = pgTable('table_name', {...})` | Entity definition |
| Column definition | `columnName: type('db_name')` | Property definition |
| Constraints | `.primaryKey()`, `.notNull()`, `.unique()` | Validation rules |
| References | `.references(() => otherTable.id)` | Foreign keys |
| Defaults | `.default(value)`, `.defaultNow()` | Default values |

---

## Table Detection Pattern

| Pattern | Extraction |
|---------|------------|
| `export const X = pgTable(` | Table name: `X` |
| `pgTable('db_table_name'` | Database table name |
| Content between `{` and `}` | Column definitions |

---

## Column Detection Patterns

| Pattern | Column Name | Type |
|---------|-------------|------|
| `id: uuid('id')` | `id` | uuid |
| `title: varchar('title', {length: 255})` | `title` | varchar(255) |
| `status: varchar('status', {length: 50})` | `status` | varchar(50) |
| `count: integer('count')` | `count` | integer |
| `isActive: boolean('is_active')` | `isActive` | boolean |
| `createdAt: timestamp('created_at')` | `createdAt` | timestamp |

---

## Constraint Detection

| Constraint | Pattern | C# Impact |
|------------|---------|-----------|
| Primary key | `.primaryKey()` | Mark as `Id` property |
| Not null | `.notNull()` | Non-nullable type |
| Unique | `.unique()` | Validation only |
| Default | `.default(X)` | Set in MockData |
| Default now | `.defaultNow()` | `DateTime.UtcNow` |

---

## Reference Detection

| Pattern | Extracted Info |
|---------|----------------|
| `.references(() => users.id)` | FK to `users` table, column `id` |
| `.references(() => epics.id, {onDelete: 'cascade'})` | FK with cascade delete |

---

## Enum Detection

| Pattern | Extraction |
|---------|------------|
| `export const statusEnum = pgEnum('status', ['draft', 'active', 'done'])` | Enum name: `status`, values: draft, active, done |
| Column using enum: `status: statusEnum('status')` | Column uses enum type |

---

## Parsing Steps

| Step | Action | Output |
|------|--------|--------|
| 1 | Find all `pgTable()` calls | List of table definitions |
| 2 | Extract table name from export | Entity name |
| 3 | Parse column definitions | List of (name, type, constraints) |
| 4 | Identify primary keys | Mark `Id` properties |
| 5 | Identify foreign keys | List of relationships |
| 6 | Find enum definitions | Enum types and values |
| 7 | Extract defaults | Default value mappings |

---

## Name Transformation Rules

| Source (Drizzle) | Target (C#) | Example |
|------------------|-------------|---------|
| snake_case table | PascalCase class | `user_profiles` → `UserProfile` |
| snake_case column | PascalCase property | `created_at` → `CreatedAt` |
| plural table name | singular class | `epics` → `Epic` |
| enum name | PascalCase enum | `status_enum` → `StatusEnum` |

---

## Common Schema Patterns

| Pattern | Meaning |
|---------|---------|
| `id: uuid('id').primaryKey()` | UUID primary key |
| `...timestamps` | createdAt, updatedAt columns |
| `userId: uuid('user_id').references(() => users.id)` | Foreign key to users |
| `status: varchar('status', {length: 50}).default('draft')` | Status with default |

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
