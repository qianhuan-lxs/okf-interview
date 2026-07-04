---
type: question
id: algorithms/arrays-strings/string-to-integer
title: String to Integer (atoi) 编码题
category: algorithms
subcategory: arrays-strings
difficulty: medium
tags: [string, atoi, edge-case, leetcode, coding]
languages: []
role: [ai-app, sde, backend]
companies: [拼多多]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# String to Integer (atoi) 编码题

## 问题描述
写一个方法把字符串解析为整数。输入 "1234" 返回整数 1234。然后让你测试，把测试用例范围都写一下（5 轮边界追问）。

> LeetCode 8. String to Integer (atoi)

## 输入输出 / 约束
- 去前导空格
- 可选正负号
- 跳过非数字字符后停止
- 越界返回 INT_MAX (2147483647) / INT_MIN (-2147483648)

## 解答

```python
def myAtoi(s: str) -> int:
    INT_MAX, INT_MIN = 2**31 - 1, -2**31
    i, n = 0, len(s)
    # 1. 去前导空格
    while i < n and s[i] == " ":
        i += 1
    if i == n:
        return 0
    # 2. 符号
    sign = 1
    if s[i] in "+-":
        if s[i] == "-":
            sign = -1
        i += 1
    # 3. 数字（边累加边判越界）
    num = 0
    while i < n and s[i].isdigit():
        d = ord(s[i]) - ord("0")
        # 越界预判：避免累加后再判溢出
        if num > (INT_MAX - d) // 10:
            return INT_MAX if sign == 1 else INT_MIN
        num = num * 10 + d
        i += 1
    return sign * num
```

### 测试用例（5 轮追问要点）
1. **正常**："1234" → 1234；"0" → 0；"-5" → -5
2. **空格**："   123" → 123；"   " → 0
3. **符号**："+1" → 1；"-1" → -1；"+-1" → 0；"--1" → 0
4. **非数字**："123abc" → 123；"abc123" → 0；"  12.3" → 12
5. **越界**："2147483647" → 2147483647；"2147483648" → 2147483647；"-2147483648" → -2147483648；"-2147483649" → -2147483648
6. **边界**："" → 0；"+" → 0；"  +  1" → 0（符号后有空格）

## 易错点
- 累加后再判溢出 → 已溢出，应在累加前用 `(INT_MAX - d) // 10` 预判。
- 多个符号 "+-1" 应返回 0 而非 -1。
- 前导空格但符号后又有空格不算数字。

## 延伸

## 延伸

- 关联题：[[algorithms/dynamic-programming/longest-increasing-subsequence]]
