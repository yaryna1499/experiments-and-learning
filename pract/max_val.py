def find_max(arr: list) -> int:
    # O(n)
    i = len(arr)
    for num in arr:
        if num > arr[len(arr)-i]:
            i -= 1
            max_num = num
    return max_num

print(find_max([1,2,1000, 5,2,10]))