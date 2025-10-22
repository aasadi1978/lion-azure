def split_list(input_list=[], category_length=100):
    if len(input_list) <= category_length:
        return [input_list]

    return [input_list[i:i + category_length] for i in range(0, len(input_list), category_length)]