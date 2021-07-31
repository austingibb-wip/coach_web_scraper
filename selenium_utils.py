def scroll_to(passed_in_driver, object, x_offset=0, y_offset=0):
    x = object.location['x'] - x_offset
    y = object.location['y'] - y_offset
    scroll_by_coord = 'window.scrollTo(%s,%s);' % (
        x,
        y
    )
    passed_in_driver.execute_script(scroll_by_coord)