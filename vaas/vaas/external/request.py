from inspect import stack


def get_current_request():
    for frame_record in stack():
        if frame_record[3] == 'get_response':
            return frame_record[0].f_locals['request']
    return None
