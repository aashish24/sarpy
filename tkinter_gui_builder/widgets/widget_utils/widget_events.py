class WidgetEvents:
    def __init__(self):
        pass

    # events
    def on_left_mouse_click(self, event):
        self.bind("<Button-1>", event)

    def on_left_mouse_press(self, event):
        self.bind("<ButtonPress-1>", event)

    def on_left_mouse_motion(self, event):
        self.bind("<B1-Motion>", event)

    def on_left_mouse_release(self, event):
        self.bind("<ButtonRelease-1>", event)

    def on_right_mouse_click(self, event):
        self.bind("<Button-3>", event)

    def on_right_mouse_press(self, event):
        self.bind("<ButtonPress-3>", event)

    def on_right_mouse_motion(self, event):
        self.bind("<B3-Motion>", event)

    def on_left_mouse_click_with_args(self, event_w_args, args):
        self.bind("<Button-1>", lambda event, arg=args: event_w_args(arg))

    def on_right_mouse_click_with_args(self, event_w_args, args):
        self.bind("<Button-3>", lambda event, arg=args: event_w_args(arg))