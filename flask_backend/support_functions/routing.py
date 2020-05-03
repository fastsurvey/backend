
def get_params_dict(request, print_out=False):

    try:
        params_dict = request.get_json(force=True)
    except:
        params_dict = {}

    if not isinstance(params_dict, dict):
        params_dict = {}

    params_dict.update(dict(request.form))
    params_dict.update(dict(request.files))

    for key in ['email', 'api_key', 'password']:
        if key not in params_dict:
            params_dict.update({key: None})

    params_dict.update({'method': request.method})

    query_string_list = request.query_string.decode().split('&')

    for query_string_element in query_string_list:

        element_list = query_string_element.split('=')

        if len(element_list) != 2:
            continue

        element_list[0] = element_list[0].strip()
        element_list[1] = element_list[1].strip()
        if len(element_list[0]) == 0 or len(element_list[1]) == 0:
            continue

        if ',' in element_list[1]:
            element_list[1] = list(filter(lambda x: len(x) != 0, element_list[1].split(',')))

        params_dict[element_list[0]] = element_list[1]

    if print_out:
        print('\n\n')
        print(params_dict)

    return params_dict
