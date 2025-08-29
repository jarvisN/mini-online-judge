from __future__ import annotations

from typing import Any, Dict, List, Optional


# Problem bank
# Each problem:
# - id: str
# - title: str
# - description: str
# - function_name: str
# - function_signature: str (e.g., "def two_sum(nums, target):")
# - template_code: str
# - tests: List[{"args": [...], "kwargs": {...}, "expected": Any | List[Any]}]


PROBLEMS: Dict[str, Dict[str, Any]] = {}


def _add_problem(p: Dict[str, Any]) -> None:
    PROBLEMS[p["id"]] = p


_add_problem(
    {
        "id": "two_sum",
        "title": "Two Sum (Easy)",
        "description": (
            "ให้เขียนฟังก์ชันค้นหาคู่ของตัวเลขในลิสต์ที่รวมกันได้เท่ากับ target "
            "และคืนค่า index ของทั้งสองตำแหน่ง (ลำดับอาจแตกต่างได้)\n\n"
            "ข้อกำหนด:\n"
            "- ให้คืนค่าเป็นลิสต์ความยาว 2 ของ index เช่น [i, j]\n"
            "- ห้ามใช้การ import ใดๆ\n"
        ),
        "function_name": "two_sum",
        "function_signature": "def two_sum(nums, target):",
        "template_code": (
            "def two_sum(nums, target):\n"
            "    # ใช้ hash map เพื่อลดเวลาเป็น O(n)\n"
            "    seen = {}\n"
            "    for i, x in enumerate(nums):\n"
            "        need = target - x\n"
            "        if need in seen:\n"
            "            return [seen[need], i]\n"
            "        seen[x] = i\n"
            "    return []\n"
        ),
        "tests": [
            {"args": [[2, 7, 11, 15], 9], "kwargs": {}, "expected": [[0, 1], [1, 0]]},
            {"args": [[3, 2, 4], 6], "kwargs": {}, "expected": [[1, 2], [2, 1]]},
            {"args": [[3, 3], 6], "kwargs": {}, "expected": [[0, 1], [1, 0]]},
        ],
    }
)

_add_problem(
    {
        "id": "fibonacci",
        "title": "Fibonacci N (Easy)",
        "description": (
            "ให้เขียนฟังก์ชันคืนค่าเลขฟีโบนัชชีลำดับที่ n (เริ่ม F0=0, F1=1)\n\n"
            "ข้อกำหนด:\n"
            "- อินพุต n เป็นจำนวนเต็มไม่ลบ\n"
            "- ห้ามใช้การ import ใดๆ\n"
        ),
        "function_name": "fib",
        "function_signature": "def fib(n):",
        "template_code": (
            "def fib(n):\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        a, b = b, a + b\n"
            "    return a\n"
        ),
        "tests": [
            {"args": [0], "kwargs": {}, "expected": 0},
            {"args": [1], "kwargs": {}, "expected": 1},
            {"args": [7], "kwargs": {}, "expected": 13},
            {"args": [10], "kwargs": {}, "expected": 55},
        ],
    }
)

_add_problem(
    {
        "id": "is_palindrome",
        "title": "Is Palindrome (String)",
        "description": (
            "ให้เขียนฟังก์ชันตรวจว่าข้อความเป็น palindrome หรือไม่ (ไม่สนช่องว่าง/เครื่องหมาย/ตัวพิมพ์)\n\n"
            "ข้อกำหนด:\n"
            "- คืนค่า True/False\n"
        ),
        "function_name": "is_palindrome",
        "function_signature": "def is_palindrome(s):",
        "template_code": (
            "def is_palindrome(s):\n"
            "    t = ''.join(ch.lower() for ch in s if ch.isalnum())\n"
            "    return t == t[::-1]\n"
        ),
        "tests": [
            {"args": ["A man, a plan, a canal: Panama"], "kwargs": {}, "expected": True},
            {"args": ["race a car"], "kwargs": {}, "expected": False},
            {"args": [""], "kwargs": {}, "expected": True},
        ],
    }
)


def list_problems() -> List[Dict[str, Any]]:
    # Minimal projection for UI + embed all needed fields
    items = []
    for pid, p in PROBLEMS.items():
        items.append(
            {
                "id": pid,
                "title": p["title"],
                "description": p["description"],
                "function_name": p["function_name"],
                "function_signature": p["function_signature"],
                "template_code": p["template_code"],
            }
        )
    # Keep stable ordering
    items.sort(key=lambda x: x["id"]) 
    return items


def get_problem(pid: str) -> Optional[Dict[str, Any]]:
    return PROBLEMS.get(pid)

