import math

def bell_curve_height(x, coef, power_coef, mean):
    numer = -((x - mean) ** 2)
    power = numer / power_coef
    return math.pow(math.e, power) / coef

def generate_bell_curve(mean, stddev, minx, maxx, step):
    coef = math.sqrt(2 * math.pi * stddev * stddev)
    power_coef = 2 * stddev * stddev

    bell_curve = []
    x = minx
    while x <= maxx:
        if stddev == 0:
            bell_curve.append(0)
        else:
            bell_curve.append(bell_curve_height(x, coef, power_coef, mean))
        x += step

    return bell_curve

def create_bell_curve_labels(minx, maxx, step=0.2):
    labels = []
    x = minx
    while x <= maxx:
        labels.append(f"{x:.2f}")
        x += step
    
    return labels

def create_bell_curve_dataset(label, datapoints, minx=None, maxx=None, step=0.2, color="#dedede"):
    if minx is None:
        minx = min(datapoints)
    
    if maxx is None:
        maxx = max(datapoints)

    mean = sum(datapoints) / len(datapoints)
    stddev = math.sqrt(
        sum((x - mean) ** 2 for x in datapoints) / (len(datapoints) - 1)
    )

    data = generate_bell_curve(mean, stddev, minx, maxx, step)

    return {
        "label": label,
        "data": data,
        "fill": False,
        "borderColor": color,
        "tension": 0.1,
        "pointRadius": 0
    }
