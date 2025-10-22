def split_string(txt, line_length=120):

    try:
        if not txt:
            return ""

        str_list = []

        while len(txt) > line_length:

            txt2 = txt[:line_length]
            idx_last_space = txt2.rfind(' ')

            if idx_last_space == -1:
                new_row = txt2
                txt = txt[line_length:]
            else:
                new_row = txt[:idx_last_space]
                txt = txt[idx_last_space + 1:]

            str_list.append(new_row)

        str_list.append(txt)

        return '\n'.join(str_list)

    except Exception:
        return txt