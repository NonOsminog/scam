import math
import random
import asyncio

async def getNumberRand():
    rangeNumber = [900, 901, 902, 903, 904, 905, 906, 908, 909, 910,
                   911, 912, 913, 914, 915, 916, 917, 918, 919, 920,
                   921, 922, 923, 924, 925, 926, 927, 928, 929, 930,
                   931, 932, 933, 934, 936, 937, 938, 939, 941, 950,
                   951, 952, 953, 954, 955, 958, 960, 961, 962, 963,
                   964, 965, 966, 967, 968, 969, 970, 971, 977, 978,
                   980, 981, 982, 983, 984, 985, 986, 987, 988, 989,
                   991, 992, 993, 994, 995, 996, 997, 999]
    return f"7{random.choice(rangeNumber)}{random.randint(0000000, 9999999)}"

async def getStatus(stat):
    if stat == 0:
        status = 'Воркер'
        return status
    elif stat == 1:
        status = 'Юнга'
        return status
    elif stat == 2:
        status = 'Матрос'
        return status
    elif stat == 3:
        status = 'Корсар'
        return status
    elif stat == 4:
        status = 'Штурман'
        return status
    elif stat == 5:
        status = 'Капитан'
        return status

async def workStatus(work_status):
    if work_status == 'true':
        status = '⚡️ FULL WORK ⚡️'
        return status
    elif work_status == 'false':
        status = '☠️ NOT WORK ☠️'
        return status

# def dateStringEnds(day):
#     if day % 10 == 1 and day % 100 != 11:
#         ends = "день"
#     elif day % 10 == 0 or day % 10 in [2, 3, 4, 5, 6, 7, 8, 9] or day % 100 in [11, 12, 13, 14]:
#         ends = "дней"
#     return(ends)