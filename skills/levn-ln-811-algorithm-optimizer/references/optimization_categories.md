# Optimization Categories Checklist

<!-- SCOPE: Hypothesis generation checklist for algorithm optimization. Categories to scan when generating optimization ideas. -->
<!-- DO NOT add here: optimization workflow → ln-811-algorithm-optimizer SKILL.md -->

Systematic checklist for generating optimization hypotheses. Scan each category against target function.

---

## Categories

### 1. Algorithmic Complexity

| Pattern | Symptom | Optimization |
|---------|---------|-------------|
| O(n^2) nested loops | Nested iteration over same collection | Hash map lookup O(1), sorting + binary search O(n log n) |
| Linear search | Sequential scan for known key | Index, hash set, binary search |
| Repeated computation | Same calculation in loop body | Memoization, pre-computation, lookup table |
| Unnecessary sorting | Sort where partial order suffices | Heap / quickselect for top-K |

### 2. Memory & Allocation

| Pattern | Symptom | Optimization |
|---------|---------|-------------|
| Frequent small allocations | `new` / append in tight loop | Pre-allocate buffer, object pooling |
| String concatenation | `+=` string in loop | StringBuilder / join / format |
| Unnecessary copies | Value-type passed where ref suffices | Pass by reference / pointer |
| Large intermediate collections | Filter then map creates 2 lists | Lazy evaluation / generators / iterators |

### 3. Cache & Data Locality

| Pattern | Symptom | Optimization |
|---------|---------|-------------|
| Random access on large data | Pointer chasing, linked list traversal | Array-based layout, struct-of-arrays |
| Cold cache access | First access always slow | Data prefetching, batch processing |
| Branch misprediction | Conditional in hot loop | Branchless alternatives, lookup tables |

### 4. I/O & Concurrency

| Pattern | Symptom | Optimization |
|---------|---------|-------------|
| Sequential I/O | One-at-a-time file/network ops | Batch, parallel, async |
| Blocking in async context | `sleep()`, sync I/O in async func | `asyncio.sleep()`, `aiofiles`, `to_thread()` |
| Lock contention | Shared mutable state in hot path | Lock-free structures, partitioning |

### 5. Language-Specific

| Language | Pattern | Optimization |
|----------|---------|-------------|
| Python | Global interpreter lock (GIL) | `multiprocessing`, C extension, numpy vectorization |
| Python | List comprehension vs loop | List comprehension (2-3x faster) |
| Go | Interface dispatch in hot path | Concrete type, generics |
| JS/TS | `JSON.parse`/`stringify` in loop | Structured clone, manual serialization |
| .NET | Boxing value types | Generic constraints, `Span<T>` |
| Rust | Unnecessary `.clone()` | Borrow, lifetime annotations |

### 6. Data Structure Selection

| Current | Alternative | When |
|---------|-------------|------|
| Array/List | Hash Set | Frequent membership tests |
| Hash Map | Sorted Array | Small collections (< 50 elements) |
| Linked List | Array/Vec | Sequential access, cache locality |
| Tree (balanced) | Hash Map | No ordering needed |
| String keys | Integer/Enum keys | Fixed set of keys |

---

## Hypothesis Generation Protocol

1. Read target function code
2. For each category above: check if any pattern matches
3. For each match: create hypothesis with expected_impact estimate
4. Cross-reference with MCP research findings
5. Deduplicate (same fix from multiple categories = one hypothesis)
6. Order by expected_impact DESC, risk ASC

---

**Version:** 1.0.0
**Last Updated:** 2026-03-08
