from layouteditor import wrapper


def main():
    layout = wrapper.Layout()
    drawing = layout.drawing()
    return layout, drawing

if __name__ == '__main__':
    layout, drawing = main()
