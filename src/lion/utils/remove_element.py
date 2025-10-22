def remove_element(mylist, elem):
    try:
        mylist.remove(elem)
    except Exception:
        pass

    return mylist