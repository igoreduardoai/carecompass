from alexa_sim import amounts, nums
g = nums({"total": 551.0, "installments": [183.67, 183.67, 183.66]})
R = [amounts("You owe $551 in 3 payments of $183.67") <= g,
     sorted(amounts("You owe $560.00") - g) == [560.0],
     amounts("$1,234.50 due") == {1234.5}]
print(R, f"{sum(R)}/{len(R)} passed")
