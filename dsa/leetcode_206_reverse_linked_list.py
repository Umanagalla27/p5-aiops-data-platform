"""LeetCode 206: Reverse Linked List.

Given the head of a singly linked list, reverse the list, and return the reversed list.

Core Concept:
    In-place pointer manipulation tracking `prev`, `curr`, and `next_temp` in O(N) time
    and O(1) auxiliary memory.
"""

from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next_node: Optional["ListNode"] = None):
        self.val = val
        self.next = next_node


class Solution:
    def reverseList(self, head: ListNode | None) -> ListNode | None:
        """Reverses a singly-linked list iteratively in O(N) time and O(1) auxiliary space."""
        prev: ListNode | None = None
        curr: ListNode | None = head

        while curr is not None:
            next_temp = curr.next
            curr.next = prev
            prev = curr
            curr = next_temp

        return prev


def _list_to_nodes(values: list[int]) -> ListNode | None:
    dummy = ListNode(0)
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def _nodes_to_list(head: ListNode | None) -> list[int]:
    result = []
    curr = head
    while curr is not None:
        result.append(curr.val)
        curr = curr.next
    return result


if __name__ == "__main__":
    head = _list_to_nodes([1, 2, 3, 4, 5])
    reversed_head = Solution().reverseList(head)
    assert _nodes_to_list(reversed_head) == [5, 4, 3, 2, 1]
    print("[DSA] LeetCode 206 Reverse Linked List passed successfully!")
