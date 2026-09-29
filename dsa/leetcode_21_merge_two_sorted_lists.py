"""LeetCode 21: Merge Two Sorted Lists.

Merge two sorted linked lists and return it as a sorted list.
The list should be made by splicing together the nodes of the first two lists.

Core Concept:
    Dummy head pointer comparing heads of both lists iteratively in O(N + M) time
    and O(1) auxiliary space.
"""

from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next_node: Optional["ListNode"] = None):
        self.val = val
        self.next = next_node


class Solution:
    def mergeTwoLists(self, list1: ListNode | None, list2: ListNode | None) -> ListNode | None:
        """Merges two sorted linked lists iteratively using a dummy head pointer."""
        dummy = ListNode(-1)
        tail = dummy

        while list1 is not None and list2 is not None:
            if list1.val <= list2.val:
                tail.next = list1
                list1 = list1.next
            else:
                tail.next = list2
                list2 = list2.next
            tail = tail.next

        # Attach remaining nodes
        tail.next = list1 if list1 is not None else list2

        return dummy.next


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
    l1 = _list_to_nodes([1, 2, 4])
    l2 = _list_to_nodes([1, 3, 4])
    merged = Solution().mergeTwoLists(l1, l2)
    assert _nodes_to_list(merged) == [1, 1, 2, 3, 4, 4]
    print("[DSA] LeetCode 21 Merge Two Sorted Lists passed successfully!")
