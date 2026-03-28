# Algorithm Patterns

Reference guide. Read the pattern that matches your problem before coding.

## String Operations
- **Iterate chars**: `for c in s` or `for i, c in enumerate(s)`
- **Case insensitive**: always `.lower()` or `.upper()` first
- **Split words**: `s.split()` handles multiple spaces; `s.split(' ')` does not
- **Reverse**: `s[::-1]` for string, `' '.join(s.split()[::-1])` for word order

## Hash Maps (dict)
- **When to use**: need O(1) lookup by key, counting, grouping, complement search
- **Two-sum pattern**: `seen = {}; for i, n in enumerate(nums): if target-n in seen: found`
- **Counting**: `counts = {}; for x in items: counts[x] = counts.get(x, 0) + 1`
- **Grouping**: `groups = {}; for x in items: groups.setdefault(key(x), []).append(x)`

## Arrays / Lists
- **Remove duplicates preserving order**: `seen = set(); [x for x in lst if not (x in seen or seen.add(x))]`
- **Sliding window**: two pointers `left, right` moving through array
- **Kadane's (max subarray)**: `cur = max_sum = nums[0]; for n in nums[1:]: cur = max(n, cur+n); max_sum = max(max_sum, cur)`
- **Two pointers**: sort first, then `left=0, right=len-1`, move inward

## Sorting
- **Selection sort**: find min in remaining, swap to front. O(n²)
- **Merge sort**: split in half, sort each, merge. O(n log n)
- **Key insight**: if you need "sort without built-in", implement selection sort (simplest)

## Searching
- **Binary search**: `lo, hi = 0, len(arr)-1; while lo <= hi: mid = (lo+hi)//2`
- **Key insight**: array MUST be sorted. Check `arr[mid]` vs target, move lo or hi

## Recursion
- **Base case first**: what stops the recursion? (empty list, n=0, leaf node)
- **Recursive case**: break problem into smaller same-shaped problem
- **Memoization**: `memo = {}; if n in memo: return memo[n]`
- **Flatten nested**: `if isinstance(item, list): result.extend(flatten(item)) else: result.append(item)`

## Dynamic Programming
- **When to use**: overlapping subproblems + optimal substructure
- **Bottom-up**: build table from smallest to largest
- **LCS**: `dp[i][j] = dp[i-1][j-1]+1 if match else max(dp[i-1][j], dp[i][j-1])`
- **Key insight**: define what `dp[i]` means in words before coding

## Graphs
- **Union-Find**: `parent = list(range(n)); find(x): while parent[x]!=x: x=parent[x]`
- **BFS**: `queue = [start]; while queue: node = queue.pop(0); visit neighbors`
- **DFS**: `visited = set(); def dfs(node): visited.add(node); for neighbor: dfs(neighbor)`
- **Connected components**: union-find or DFS from each unvisited node

## Data Structures
- **Stack**: `list` with `.append()` and `.pop()`. LIFO.
- **Queue**: `collections.deque` with `.append()` and `.popleft()`. FIFO.
- **Set**: O(1) membership test. Use for dedup, seen-tracking.

## Common Edge Cases
- Empty input: `[]`, `""`, `0`, `None`
- Single element: `[1]`, `"a"`
- All same: `[5,5,5,5]`
- Negative numbers: `[-1,-2,-3]`
- Duplicates: `[1,1,2,2]`
- `True == 1` and `False == 0` in Python (set/dict trap)
