import random
import copy

def get_santa(data):
    from_list = random.sample(data, len(data))
    to_list = copy.copy(from_list)
    to_list.append(to_list.pop(0))
    # results = []
    # for i in range(len(ids)):
    #     results.append((from_list[i], to_list[i]))
    results = {}
    for i in range(len(data)):
        results[from_list[i]] = to_list[i]
    return results