from datetime import datetime, timedelta

def group_data_by_day(datapoint_source, max_days, get_id, get_score=lambda x: x.score, get_time=lambda x: x.time):
    
    days = None
    ids = set()
    for datapoint in datapoint_source:
        date = get_time(datapoint).date()
        if days is None:
            days = [(date - timedelta(days=day_offset), {}) for day_offset in range(max_days)]

        day_data = None
        for day in days:
            if date == day[0]:
                day_data = day[1]
                break
        
        if day_data is None:
            break

        id = get_id(datapoint)
        ids.add(id)
        if id not in day_data:
            day_data[id] = get_score(datapoint)

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


