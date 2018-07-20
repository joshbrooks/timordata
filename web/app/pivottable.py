def pivot_table(cls, _filter=None, field_name="activity", relation_data=None):

    if _filter:
        queryset = cls.objects.filter(**_filter).prefetch_related(field_name)
    else:
        queryset = cls.objects.all().prefetch_related(field_name)
    if not relation_data:
        relation_data = getattr(cls, field_name).field.get_choices()

    relations_index = {}
    relations_index_reversed = {}
    relations_label = {}
    relations_counts = {}

    # Create a count of each property
    count_set = list(queryset.values_list(field_name, flat=True))

    for i in set(count_set):
        relations_counts[i] = count_set.count(i)

    for k, v in enumerate(relation_data):
        relations_index[v[0]] = k
        relations_label[k] = {"name": v[1], "count": relations_counts.get(v[0])}

    queryset_data = {}
    for item in queryset:
        queryset_data[item.pk] = {"object": item, "data": [False] * len(relation_data)}

    for item_pk, attr in queryset.values_list("pk", field_name):
        if not attr:
            continue
        try:
            i = relations_index[attr]
            queryset_data[item_pk]["data"][i] = True
        except KeyError:
            continue

    return {"labels": relations_label, "data": list(queryset_data.items())}
