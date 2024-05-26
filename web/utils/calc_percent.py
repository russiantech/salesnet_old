
"""  Calculate percentage in Python
To calculate a percentage in Python:

Use the division / operator to divide one number by another.
Multiply the quotient by 100 to get the percentage.
The result shows what percent the first number is of the second. """

def cal_percent(x, y):
    try:
        pcnt = (x / y ) * 100
        #return "{:.2f}%".format(pcnt)
        return "{:.2f}%".format(pcnt)
    except ZeroDivisionError:
        return 0


""" print(cal_percent(60, 0))  # 👉️ inf
print(cal_percent(60, 60))  # 👉️ 0.0
print(cal_percent(60, 120))  # 👉️ 50.0 """