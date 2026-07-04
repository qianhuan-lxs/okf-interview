---
type: question
id: algorithms/dynamic-programming/longest-increasing-subsequence
title: 最长递增子序列 (LIS)
category: algorithms
subcategory: dynamic-programming
difficulty: medium
tags: [dynamic-programming, binary-search, patience-sorting]
languages: [python, cpp]
role: [sde, backend]
companies: [Google, ByteDance]
source: leetcode-300
status: reviewed
timestamp: 2026-07-04
---

# 最长递增子序列 (LIS)

## 问题描述

给定一个整数数组 `nums`，找到其中**最长严格递增子序列**的长度。

LeetCode: https://leetcode.cn/problems/longest-increasing-subsequence/

## 输入输出 / 约束

```
输入: nums = [10,9,2,5,3,7,101,18]
输出: 4
解释: 最长递增子序列是 [2,3,7,101]，长度为 4。

约束:
- 1 <= nums.length <= 2500
- -10^4 <= nums[i] <= 10^4
```

进阶：能否把时间复杂度降到 O(n log n)？

## 思路

两种思路对比：

1. **DP — O(n²)**：`dp[i]` 表示以 `nums[i]` 结尾的 LIS 长度。对每个 `i` 扫一遍 `j < i`，若 `nums[j] < nums[i]` 则 `dp[i] = max(dp[i], dp[j] + 1)`。
2. **Patience Sorting — O(n log n)**：维护一个数组 `tails`，`tails[k]` 表示长度为 `k+1` 的所有递增子序列中**最小结尾**。对每个 `x`，在 `tails` 上二分找第一个 `>= x` 的位置并替换；若 `x` 比所有都大则追加。最终 `len(tails)` 即答案。

## 解答

### 解法一：DP

```python
def lengthOfLIS(nums: list[int]) -> int:
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
```

### 解法二：Patience Sorting + 二分

```python
import bisect

def lengthOfLIS(nums: list[int]) -> int:
    tails: list[int] = []
    for x in nums:
        i = bisect.bisect_left(tails, x)  # 严格递增用 left；非严格用 right
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
```

## 复杂度

- 解法一：时间 O(n²)，空间 O(n)
- 解法二：时间 O(n log n)，空间 O(n)

## 易错点

- "严格递增" 用 `bisect_left`；"非严格递增" 用 `bisect_right`。这是最常见踩坑点。
- DP 解法的 `dp[i]` 是**以 `i` 结尾**的 LIS，不是全局 LIS，最后要再取 `max(dp)`。
- `tails` 数组**不是**真正的 LIS，只是长度等于 LIS 长度。要还原序列需额外维护 predecessor 指针。

## 延伸

- 关联题：[[algorithms/dynamic-programming/longest-common-subsequence]]
- 进阶题：[[algorithms/dynamic-programming/russian-doll-envelopes]]（二维 LIS）
- 变体：[[algorithms/dynamic-programming/number-of-longest-increasing-subsequence]]
