
def group_data_by_day(datapoint_source, max_days, get_id, get_score=lambda x: x.score, get_time=lambda x: x.time):
    days = []
    ids = set()
    for datapoint in datapoint_source:
        print(datapoint)
        time = get_time(datapoint)
        if not days or days[-1][0] != time.date():
            if len(days) >= max_days:
                break
            days.append((time.date(), {}))
        
        day_data = days[-1][1]
        id = get_id(datapoint)
        ids.add(id)
        if id not in day_data:
            day_data[id] = get_score(datapoint)
    print(days)

    days = days[::-1]

    datasets = []
    # fill in gaps
    for id in ids:
        first_value = 0
        for _, day_data in days:
            if id in day_data:
                first_value = day_data[id]
                break
        data = []
        current_value = first_value
        for _, day_data in days:
            if id in day_data:
                current_value = day_data[id]
            else:
                day_data[id] = current_value
            data.append(day_data[id])
        datasets.append((id, data))
    
    labels = [time.strftime("%d/%m/%Y") for time, _ in days]
    return labels, datasets


