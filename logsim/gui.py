"""Implement the graphical user interface for the Logic Simulator.

Used in the Logic Simulator project to enable the user to run the simulation,
continue the simulation, stop a running simulation, and type commands into a
small terminal-style input box.

Classes:
--------
MyGLCanvas - handles all canvas drawing operations.
Gui - configures the main window and all the widgets.
"""
import wx
import wx.glcanvas as wxcanvas
from OpenGL import GL, GLUT

from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations.

    This class contains functions for drawing onto the canvas. It also contains
    handlers for events relating to the canvas.

    Parameters
    ----------
    parent: parent window.
    devices: instance of the devices.Devices() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    init_gl(self): Configures the OpenGL context.

    render(self, text): Handles all drawing operations.

    on_paint(self, event): Handles the paint event.

    on_size(self, event): Handles the canvas resize event.

    on_mouse(self, event): Handles mouse events.

    render_text(self, text, x_pos, y_pos): Handles text drawing operations.
    """

    def __init__(self, parent, devices, monitors):
        """Initialise canvas properties and useful variables."""
        super().__init__(parent, -1,
                         attribList=[wxcanvas.WX_GL_RGBA,
                                     wxcanvas.WX_GL_DOUBLEBUFFER,
                                     wxcanvas.WX_GL_DEPTH_SIZE, 16, 0])
        GLUT.glutInit()
        self.init = False
        self.context = wxcanvas.GLContext(self)

        # Store references to simulator objects.

        self.devices = devices
        self.monitors = monitors

        # Text displayed in the canvas. This is updated by the Gui class.
        self.display_text = "Logic simulator canvas"

        # Initialise variables for panning.
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # Initialise variables for zooming.
        self.zoom = 1

        # Bind events to the canvas.
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def init_gl(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def render(self, text=None):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices.
            self.init_gl()
            self.init = True

        if text is not None:
            self.display_text = text

        size = self.GetClientSize()

        # Clear everything.
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # Draw useful status text at the top-left of the canvas.
        self.render_text(self.display_text, 10, size.height - 20)
        self.draw_monitor_traces()

        # We have been drawing to the back buffer, so flush the graphics
        # pipeline and swap the back buffer to the front.
        GL.glFlush()
        self.SwapBuffers()

    def draw_monitor_traces(self):
        """Draw the monitor trace from self.device."""
        start_x = 100
        start_y = 230
        step_x = 25
        trace_gap = 60
        trace_height = 25

        # Draw each monitored signal on a separate horizontal line.
        for trace_index, (device_id, output_id) in enumerate(
                self.monitors.monitors_dictionary):

            signal_list = self.monitors.monitors_dictionary[
                (device_id, output_id)]

            # Get a readable signal name
            signal_name = self.devices.get_signal_name(device_id, output_id)

            low_y = start_y - trace_index * trace_gap
            high_y = low_y + trace_height

            # Draw the signal name on the left.
            self.render_text(signal_name, 10, low_y)
            self.render_text("1", 50, high_y)
            self.render_text("0", 50, low_y)
            GL.glColor3f(0.0, 0.0, 1.0)
            GL.glBegin(GL.GL_LINE_STRIP)

            for i, signal in enumerate(signal_list):
                x = start_x + i * step_x

                if signal == self.devices.HIGH:
                    y = high_y
                elif signal == self.devices.LOW:
                    y = low_y
                elif signal == self.devices.RISING:
                    y = high_y
                elif signal == self.devices.FALLING:
                    y = low_y
                elif signal == self.devices.BLANK:
                    y = low_y
                else:
                    y = low_y

                GL.glVertex2f(x, y)

            GL.glEnd()

    def on_paint(self, event):
        """Handle the paint event."""
        self.SetCurrent(self.context)
        if not self.init:
            # Configure the viewport, modelview and projection matrices.
            self.init_gl()
            self.init = True

        self.render()

    def on_size(self, event):
        """Handle the canvas resize event."""
        # Forces reconfiguration of the viewport, modelview and projection
        # matrices on the next paint event.
        self.init = False
        self.Refresh()

    def on_mouse(self, event):
        """Handle mouse events."""
        text = ""

        # Calculate object coordinates of the mouse position.
        size = self.GetClientSize()
        ox = (event.GetX() - self.pan_x) / self.zoom
        oy = (size.height - event.GetY() - self.pan_y) / self.zoom
        old_zoom = self.zoom

        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            text = "".join(["Mouse button pressed at: ", str(event.GetX()),
                            ", ", str(event.GetY())])

        if event.ButtonUp():
            text = "".join(["Mouse button released at: ", str(event.GetX()),
                            ", ", str(event.GetY())])

        if event.Leaving():
            text = "".join(["Mouse left canvas at: ", str(event.GetX()),
                            ", ", str(event.GetY())])

        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False
            text = "".join(["Mouse dragged to: ", str(event.GetX()),
                            ", ", str(event.GetY()), ". Pan is now: ",
                            str(self.pan_x), ", ", str(self.pan_y)])

        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position.
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = "".join(["Negative mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])

        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (
                event.GetWheelRotation() / (20 * event.GetWheelDelta())))
            # Adjust pan so as to zoom around the mouse position.
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = "".join(["Positive mouse wheel rotation. Zoom is now: ",
                            str(self.zoom)])

        if text:
            self.render(text)
        else:
            self.Refresh()

    def render_text(self, text, x_pos, y_pos):
        """Handle text drawing operations."""
        GL.glColor3f(0.0, 0.0, 0.0)
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            if character == "\n":
                y_pos = y_pos - 20
                GL.glRasterPos2f(x_pos, y_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

    def set_horizontal_scroll(self, value):
        """Set horizontal pan from the scrollbar value."""
        self.pan_x = -value
        self.init = False
        self.Refresh()

    def set_vertical_scroll(self, value):
        """Set vertical pan from the scrollbar value."""
        self.pan_y = value
        self.init = False
        self.Refresh()


class Gui(wx.Frame):
    """Configure the main window and all the widgets.

    This class provides a graphical user interface for the Logic Simulator and
    enables the user to run simulations using a terminal-style command box.

    Parameters
    ----------
    title: title of the window.
    path: path of the definition file.
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.

    Public methods
    --------------
    on_menu(self, event): Event handler for the file menu.

    on_run_button(self, event): Event handler for the run button.

    on_continue_button(self, event): Event handler for the continue button.

    on_stop_button(self, event): Event handler for the stop button.

    on_text_box(self, event): Event handler for terminal text entry.
    """

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))

        # Store references to the simulator objects.

        self.path = path
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors

        self.is_running = False
        self.cycles_remaining = 0
        self.cycles_completed = 0

        # Configure the file menu.
        fileMenu = wx.Menu()
        menuBar = wx.MenuBar()
        fileMenu.Append(wx.ID_ABOUT, "&About")
        fileMenu.Append(wx.ID_EXIT, "&Exit")
        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)

        # Create the main canvas. This occupies the top 2/3 of the window.
        self.canvas = MyGLCanvas(self, devices, monitors)
        canvas_panel = wx.Panel(self)
        canvas_outer_sizer = wx.BoxSizer(wx.VERTICAL)

        canvas_row_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.canvas = MyGLCanvas(canvas_panel, devices, monitors)

        self.v_scroll = wx.Slider(
            canvas_panel,
            wx.ID_ANY,
            value=0,
            minValue=0,
            maxValue=1000,
            style=wx.SL_VERTICAL
        )

        self.h_scroll = wx.Slider(
            canvas_panel,
            wx.ID_ANY,
            value=0,
            minValue=0,
            maxValue=1000,
            style=wx.SL_HORIZONTAL
        )

        canvas_row_sizer.Add(self.canvas, 1, wx.EXPAND)
        canvas_row_sizer.Add(self.v_scroll, 0, wx.EXPAND | wx.LEFT, 5)

        canvas_outer_sizer.Add(canvas_row_sizer, 1, wx.EXPAND | wx.ALL, 5)
        canvas_outer_sizer.Add(self.h_scroll, 0, wx.EXPAND |
                               wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        canvas_panel.SetSizer(canvas_outer_sizer)

        self.h_scroll.Bind(wx.EVT_SLIDER, self.on_horizontal_scroll)
        self.v_scroll.Bind(wx.EVT_SLIDER, self.on_vertical_scroll)

        # Create the bottom terminal panel.
        terminal_panel = wx.Panel(self)
        terminal_sizer = wx.BoxSizer(wx.VERTICAL)

        # Toolbar row above the command box.
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.run_button = wx.Button(terminal_panel, wx.ID_ANY, "Run")
        self.continue_button = wx.Button(terminal_panel, wx.ID_ANY,
                                         "Continue")
        self.stop_button = wx.Button(terminal_panel, wx.ID_ANY, "Stop")

        toolbar_sizer.Add(self.run_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.continue_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.stop_button, 0, wx.RIGHT, 5)

        # A small read-only box for status messages and command feedback.
        self.output_box = wx.TextCtrl(terminal_panel, wx.ID_ANY, "",
                                      style=wx.TE_MULTILINE |
                                      wx.TE_READONLY)

        # Read-only box showing the current value of each switch.
        self.switch_box = wx.TextCtrl(
            terminal_panel,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_READONLY)

        # The terminal input. The user can type commands such as r 10, c 5,
        # s SW1 1, m G1, z G1 and q.
        self.text_box = wx.TextCtrl(terminal_panel, wx.ID_ANY, "",
                                    style=wx.TE_PROCESS_ENTER)

        # Add the toolbar row at the top of the terminal panel.
        terminal_sizer.Add(toolbar_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Put the info box and output box side by side.
        info_output_sizer = wx.BoxSizer(wx.HORIZONTAL)

        info_output_sizer.Add(self.output_box, 2, wx.EXPAND)
        info_output_sizer.Add(self.switch_box, 1, wx.EXPAND | wx.RIGHT, 5)

        # Add the side-by-side boxes to the terminal panel.
        terminal_sizer.Add(info_output_sizer, 1, wx.EXPAND |
                           wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Add the command input box underneath.
        terminal_sizer.Add(self.text_box, 0, wx.EXPAND |
                           wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        terminal_panel.SetSizer(terminal_sizer)

        # Main vertical layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(canvas_panel, 2, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(terminal_panel, 1, wx.EXPAND | wx.ALL, 5)

        # Bind events to widgets.
        self.Bind(wx.EVT_MENU, self.on_menu)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_button)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)
        self.h_scroll.Bind(wx.EVT_SLIDER, self.on_horizontal_scroll)
        self.v_scroll.Bind(wx.EVT_SLIDER, self.on_vertical_scroll)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)
        self.Layout()
        self.write_output("Ready. Type h for help")
        self.update_switch_box()

        self.h_scroll.Bind(wx.EVT_SLIDER, self.on_horizontal_scroll)
        self.v_scroll.Bind(wx.EVT_SLIDER, self.on_vertical_scroll)

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        if Id == wx.ID_ABOUT:
            message = "Logic Simulator designed by group 14\n"
            message += "Definition file used: " + str(self.path)
            wx.MessageBox(message,
                          "About Logsim", wx.ICON_INFORMATION | wx.OK)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button.

        If the text box contains a command, this button processes it. If the
        text box is empty, it performs a default fresh run for 10 cycles.
        """
        command = self.text_box.GetValue().strip()
        if not command:
            command = "r 20"
        self.process_command(command)
        self.text_box.Clear()

    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button.

        If the text box contains a number, it is used as the number of cycles.
        Otherwise the button performs a default continue for 10 cycles.
        """
        text = self.text_box.GetValue().strip()
        if text.isdigit():
            command = "c " + text
        elif text:
            command = text
        else:
            command = "c 10"
        self.process_command(command)
        self.text_box.Clear()

    def on_stop_button(self, event):
        """Handle the event when the user clicks the stop button."""
        self.is_running = False
        self.cycles_remaining = 0
        self.write_output("Simulation stopped by user.")
        self.canvas.render("Simulation stopped.")

    def on_text_box(self, event):
        """Handle the event when the user enters text in the terminal box."""
        command = self.text_box.GetValue().strip()
        self.process_command(command)
        self.text_box.Clear()

    def update_switch_box(self):
        """Refresh value in the switch box."""
        switch_text = "Switch values:\n"

        for device_id in self.devices.find_devices():
            device = self.devices.get_device(device_id)

        # Only display SWITCH devices.
            if device.device_kind == self.devices.SWITCH:
                switch_name = self.names.get_name_string(device_id)

                switch_value = device.switch_state

                switch_text += switch_name + " = " + str(switch_value) + "\n"
                self.switch_box.SetValue(switch_text)

    def update_scrollbars(self):
        """Update scrollbar ranges from monitor count and trace length."""
        step_x = 25
        trace_gap = 60

        canvas_size = self.canvas.GetClientSize()
        canvas_width = canvas_size.width
        canvas_height = canvas_size.height

        number_of_monitors = len(self.monitors.monitors_dictionary)

        max_cycles = 0
        max_cycles = self.cycles_completed

        total_width = max_cycles * step_x + 125
        total_height = number_of_monitors * trace_gap + 100

        max_horizontal_scroll = max(0, total_width - canvas_width)
        max_vertical_scroll = max(0, total_height - canvas_height)

        print("canvas width:", canvas_width)
        print("canvas height:", canvas_height)
        print("max cycles:", max_cycles)
        print("number of monitors:", number_of_monitors)
        print("total width:", total_width)
        print("total height:", total_height)
        print("max h scroll:", max_horizontal_scroll)
        print("max v scroll:", max_vertical_scroll)
        self.h_scroll.SetRange(0, max_horizontal_scroll)
        self.v_scroll.SetRange(0, max_vertical_scroll)

    def process_command(self, command):
        """Interpret a terminal command and call the appropriate method."""
        if not command:
            self.write_output("Error: no command entered.")
            return

        self.write_output("> " + command)
        parts = command.split()
        command_type = parts[0].lower()

        if command_type == "r":
            self.handle_run_command(parts)
        elif command_type == "c":
            self.handle_continue_command(parts)
        elif command_type == "s":
            self.handle_switch_command(parts)
        elif command_type == "m":
            self.handle_monitor_command(parts)
        elif command_type == "z":
            self.handle_zap_command(parts)
        elif command_type == "q":
            self.Close(True)
        elif command_type == "h":
            self.write_output(
                "The run button run simulation for 20 cycles\n"
                "Command list:\n"
                "Run for N cycles: r N\n"
                "Set the value of switch N: s SWN 1 or s SWN 0\n"
                "Add a monitor on Gate N: m GN\n"
                "Remove a monitor on Gate N: z GN\n"
                "Press the stop button to pause the simulation\n"
                "Press the continue button to resume the simulation"
            )
        else:
            self.write_output("Error: unknown command '" + command_type + "'.")

    def handle_run_command(self, parts):
        """Process r N: run the simulation from a fresh start."""
        cycles = self.get_cycle_argument(parts, "r N")
        if cycles is None:
            return

        self.start_simulation(cycles, cold_start=True)
        self.update_scrollbars()
        self.canvas.Refresh()

    def handle_continue_command(self, parts):
        """Process c N: continue the simulation from the current state."""
        cycles = self.get_cycle_argument(parts, "c N")
        if cycles is None:
            return

        self.start_simulation(cycles, cold_start=False)

    def handle_switch_command(self, parts):
        """Process s X N: set switch X to value N."""
        if len(parts) != 3:
            self.write_output("Error: usage is s X N, for example s SW1 1.")
            return

        switch_name = parts[1]
        try:
            switch_value = int(parts[2])
        except ValueError:
            self.write_output("Error: switch value must be 0 or 1.")
            return

        if switch_value not in [0, 1]:
            self.write_output("Error: switch value must be 0 or 1.")
            return

        self.do_set_switch(switch_name, switch_value)
        self.canvas.render("Switch " + switch_name + " set to " +
                           str(switch_value) + ".")
        # Refresh the info box after changing the switch value.
        self.update_switch_box()

    def handle_monitor_command(self, parts):
        """Process m X: add a monitor on signal X."""
        if len(parts) != 2:
            self.write_output("Error: usage is m X, for example m G1.")
            return

        signal_name = parts[1]
        self.do_add_monitor(signal_name)
        self.canvas.render("Monitor added on " + signal_name + ".")
        self.update_scrollbars()
        self.canvas.Refresh()

    def handle_zap_command(self, parts):
        """Process z X: remove the monitor on signal X."""
        if len(parts) != 2:
            self.write_output("Error: usage is z X, for example z G1.")
            return

        signal_name = parts[1]
        self.do_remove_monitor(signal_name)
        self.canvas.render("Monitor removed from " + signal_name + ".")
        self.update_scrollbars()
        self.canvas.Refresh()

    def handle_help_command(self, parts):
        """Process r N: run the simulation from a fresh start."""
        cycles = self.get_cycle_argument(parts, "h")
        if cycles is None:
            return

    def get_cycle_argument(self, parts, usage):
        """Return the number of cycles from a run or continue command."""
        if len(parts) != 2:
            self.write_output("Error: usage is " + usage + ".")
            return None

        try:
            cycles = int(parts[1])
        except ValueError:
            self.write_output("Error: number of cycles must be an integer.")
            return None

        if cycles <= 0:
            self.write_output("Error: number of cycles must be positive.")
            return None

        return cycles

    def start_simulation(self, cycles, cold_start=False):
        """Start running the network without blocking the GUI.

        The simulation is split into small steps using wx.CallLater. This is
        what lets the Stop button work while the simulation is running.
        """
        if self.is_running:
            self.write_output("Error: simulation is already running.")
            return

        if cold_start:
            self.do_prepare_fresh_run()
            self.cycles_completed = 0

        self.cycles_remaining = cycles
        self.is_running = True
        self.write_output("Running for " + str(cycles) + " cycle(s).")
        self.update_scrollbars()
        self.canvas.Refresh()
        self.run_next_cycle()

    def run_next_cycle(self):
        """Run one simulation cycle, then schedule the next cycle."""
        if not self.is_running:
            return

        if self.cycles_remaining <= 0:
            self.is_running = False
            self.write_output("Simulation finished.")
            self.canvas.render("Simulation finished after " +
                               str(self.cycles_completed) + " cycle(s).")
            return

        success = self.do_one_simulation_cycle()
        if not success:
            self.is_running = False
            self.write_output("Error: simulation failed "
                              "to reach steady state.")
            self.canvas.render("Simulation error.")
            return

        self.cycles_remaining -= 1
        self.cycles_completed += 1

        # Redraw the canvas after each cycle.
        self.canvas.render("Cycle " + str(self.cycles_completed))

        # Schedule the next cycle after a short delay.
        wx.CallLater(50, self.run_next_cycle)
        self.update_scrollbars()
        self.canvas.Refresh()

    def do_prepare_fresh_run(self):
        """Prepare the simulator for a fresh run."""
        self.monitors.reset_monitors()

        self.devices.cold_startup()

    def do_one_simulation_cycle(self):
        """Run one network cycle and record monitor signals."""
        success = self.network.execute_network()

        if success:

            self.monitors.record_signals()

        return success

    def do_set_switch(self, switch_name, switch_value):
        """Set a switch value using the devices module."""
        switch_id = self.names.query(switch_name)
        if switch_id is None:
            self.write_output("Error: unknown switch " + switch_name + ".")
            return

        self.devices.set_switch(switch_id, switch_value)
        self.write_output("Set switch " + switch_name + " to " +
                          str(switch_value) + ".")

    def do_add_monitor(self, signal_name):
        """Add a monitor on an output signal."""
        # convert a signal such as
        # G1 or D1.Q into internal device_id and output_id values.
        device_id, output_id = self.devices.get_signal_ids(signal_name)
        self.monitors.make_monitor(device_id, output_id)
        self.write_output("Added monitor on " + signal_name + ".")

    def do_remove_monitor(self, signal_name):
        """Remove a monitor from an output signal."""
        # convert a signal such as
        # G1 or D1.Q into internal device_id and output_id values.
        device_id, output_id = self.devices.get_signal_ids(signal_name)

        self.monitors.remove_monitor(device_id, output_id)
        self.write_output("Removed monitor from " + signal_name + ".")

    def on_horizontal_scroll(self, event):
        """Move the canvas view horizontally."""
        value = self.h_scroll.GetValue()
        self.canvas.set_horizontal_scroll(value)

    def on_vertical_scroll(self, event):
        """Move the canvas view vertically."""
        value = self.v_scroll.GetValue()
        self.canvas.set_vertical_scroll(value)

    def write_output(self, message):
        """Write a message into the terminal output box."""
        self.output_box.AppendText(message + "\n")


if __name__ == "__main__":
    app = wx.App()
    gui = Gui(
        "Logic Simulator GUI Test",
        path=None,
        names=None,
        devices=None,
        network=None,
        monitors=None
    )
    gui.Show()
    app.MainLoop()
