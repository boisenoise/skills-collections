# Type Mapping Reference

Mapping rules from ORM schema types to C# types.

---

## Drizzle to C# Type Mapping

| Drizzle Type | C# Type | Nullable | Default Value | Notes |
|--------------|---------|----------|---------------|-------|
| `uuid('id')` | `Guid` | No | `Guid.Empty` | Primary key |
| `uuid('ref_id')` | `Guid` | Depends | `Guid.Empty` | Foreign key |
| `varchar('name', {length: N})` | `string` | Depends | `string.Empty` | Check `.notNull()` |
| `text('description')` | `string` | Yes | `null` | Long text |
| `integer('count')` | `int` | No | `0` | Numeric |
| `bigint('amount')` | `long` | No | `0L` | Large numbers |
| `real('value')` | `float` | No | `0f` | Single precision |
| `doublePrecision('value')` | `double` | No | `0d` | Double precision |
| `numeric('price', {precision, scale})` | `decimal` | No | `0m` | Money/precise |
| `boolean('isActive')` | `bool` | No | `false` | True/false |
| `timestamp('createdAt')` | `DateTime` | No | `DateTime.MinValue` | Timestamps |
| `date('birthDate')` | `DateOnly` | No | `DateOnly.MinValue` | Date only |
| `time('startTime')` | `TimeOnly` | No | `TimeOnly.MinValue` | Time only |
| `json('metadata')` | `JsonDocument` or `string` | Yes | `null` | JSON data |
| `jsonb('data')` | `JsonDocument` or `string` | Yes | `null` | Binary JSON |

---

## Prisma to C# Type Mapping

| Prisma Type | C# Type | Nullable | Notes |
|-------------|---------|----------|-------|
| `String` | `string` | Depends on `?` | Check `@db.VarChar(N)` |
| `Int` | `int` | Depends on `?` | |
| `BigInt` | `long` | Depends on `?` | |
| `Float` | `double` | Depends on `?` | |
| `Decimal` | `decimal` | Depends on `?` | |
| `Boolean` | `bool` | Depends on `?` | |
| `DateTime` | `DateTime` | Depends on `?` | |
| `Json` | `JsonDocument` | Yes | |
| `Bytes` | `byte[]` | Yes | |

---

## TypeORM to C# Type Mapping

| TypeORM Type | C# Type | Nullable | Notes |
|--------------|---------|----------|-------|
| `@PrimaryGeneratedColumn('uuid')` | `Guid` | No | Primary key |
| `@Column('varchar')` | `string` | Depends | |
| `@Column('int')` | `int` | Depends | |
| `@Column('bigint')` | `long` | Depends | |
| `@Column('decimal')` | `decimal` | Depends | |
| `@Column('boolean')` | `bool` | No | |
| `@Column('timestamp')` | `DateTime` | Depends | |
| `@Column('json')` | `JsonDocument` | Yes | |

---

## Nullable Detection Rules

| ORM | Nullable Indicator | C# Result |
|-----|-------------------|-----------|
| Drizzle | No `.notNull()` chain | `Type?` |
| Drizzle | Has `.notNull()` | `Type` |
| Prisma | Field has `?` suffix | `Type?` |
| Prisma | No `?` suffix | `Type` |
| TypeORM | `nullable: true` | `Type?` |
| TypeORM | `nullable: false` or omitted | `Type` |

---

## Primary Key Detection

| ORM | Primary Key Indicator |
|-----|-----------------------|
| Drizzle | `.primaryKey()` method |
| Prisma | `@id` attribute |
| TypeORM | `@PrimaryColumn()` or `@PrimaryGeneratedColumn()` |

---

## Foreign Key Detection

| ORM | Foreign Key Indicator | Naming Convention |
|-----|----------------------|-------------------|
| Drizzle | `.references(() => table.id)` | `{relatedTable}Id` |
| Prisma | `@relation` attribute | `{relatedModel}Id` |
| TypeORM | `@ManyToOne()`, `@JoinColumn()` | `{relatedEntity}Id` |

---

## Default Value Handling

| ORM Default | C# Handling |
|-------------|-------------|
| `.default(value)` | Set in MockData |
| `.defaultNow()` | `DateTime.UtcNow` in MockData |
| `@default(autoincrement())` | Generate sequential |
| `@default(uuid())` | `Guid.NewGuid()` |

---

**Version:** 1.0.0
**Last Updated:** 2026-01-10
