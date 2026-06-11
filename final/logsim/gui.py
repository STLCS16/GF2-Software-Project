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
import math
import numpy as np
from OpenGL import GL, GLUT, GLU
import os
from names import Names
from devices import Devices
from network import Network
from monitors import Monitors
from scanner import Scanner
from parse import Parser

_ = wx.GetTranslation


class MyGLCanvas(wxcanvas.GLCanvas):
    """Handle all drawing operations."""

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
        self.display_text = _("Logic simulator canvas")

        # Display mode: either "2D" or "3D".
        self.trace_mode = "2D"

        # 3D rotation matrix
        self.scene_rotate = np.identity(4, "f")

        # Distance between viewer and 3D scene.
        self.depth_offset = 1000

        # Constants for OpenGL materials and lights.
        self.mat_diffuse = [0.0, 0.0, 0.0, 1.0]
        self.mat_no_specular = [0.0, 0.0, 0.0, 0.0]
        self.mat_no_shininess = [0.0]
        self.mat_specular = [0.5, 0.5, 0.5, 1.0]
        self.mat_shininess = [50.0]
        self.top_right = [1.0, 1.0, 1.0, 0.0]
        self.straight_on = [0.0, 0.0, 1.0, 0.0]
        self.no_ambient = [0.0, 0.0, 0.0, 1.0]
        self.dim_diffuse = [0.5, 0.5, 0.5, 1.0]
        self.med_diffuse = [0.75, 0.75, 0.75, 1.0]
        self.no_specular = [0.0, 0.0, 0.0, 1.0]

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
        if self.trace_mode == "2D":
            self.init_gl_2d()
        else:
            self.init_gl_3d()

    def init_gl_2d(self):
        """Configure and initialise the OpenGL context."""
        size = self.GetClientSize()
        if size.width <= 0 or size.height <= 0:
            return
        self.SetCurrent(self.context)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glClearColor(1.0, 1.0, 1.0, 0.0)
        GL.glViewport(0, 0, size.width, size.height)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glTranslated(self.pan_x, self.pan_y, 0.0)
        GL.glScaled(self.zoom, self.zoom, self.zoom)

    def init_gl_3d(self):
        """Configure OpenGL for the 3D trace view."""
        size = self.GetClientSize()
        if size.width <= 0 or size.height <= 0:
            return
        self.SetCurrent(self.context)

        GL.glViewport(0, 0, size.width, size.height)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(45, size.width / size.height, 10, 10000)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, self.med_diffuse)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, self.top_right)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_AMBIENT, self.no_ambient)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_DIFFUSE, self.dim_diffuse)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_SPECULAR, self.no_specular)
        GL.glLightfv(GL.GL_LIGHT1, GL.GL_POSITION, self.straight_on)

        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SPECULAR, self.mat_specular)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_SHININESS, self.mat_shininess)
        GL.glMaterialfv(
            GL.GL_FRONT,
            GL.GL_AMBIENT_AND_DIFFUSE,
            self.mat_diffuse)
        GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)

        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glDrawBuffer(GL.GL_BACK)
        GL.glCullFace(GL.GL_BACK)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_LIGHT1)
        GL.glEnable(GL.GL_NORMALIZE)

        GL.glTranslatef(0.0, 0.0, -self.depth_offset)
        GL.glTranslatef(self.pan_x, self.pan_y, 0.0)
        GL.glRotatef(90, 1, 0, 0)
        GL.glRotatef(90, 0, 1, 0)
        GL.glRotatef(-45, 0, 0, 1)
        GL.glMultMatrixf(self.scene_rotate)
        GL.glScalef(self.zoom, self.zoom, self.zoom)

    def render(self, text=None):
        """Handle all drawing operations."""
        self.SetCurrent(self.context)

        if text is not None:
            self.display_text = text

        if self.trace_mode == "2D":
            self.init_gl_2d()
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            size = self.GetClientSize()
            self.render_text_2d(self.display_text, 10, size.height - 20)
            self.draw_monitor_traces_2d()
            self.draw_2d_sticky_trace_labels()
        else:
            self.init_gl_3d()
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            self.draw_monitor_traces_3d()

        GL.glFlush()
        self.SwapBuffers()

    def draw_monitor_traces_2d(self):
        """Draw the monitor trace from self.monitors."""
        start_x = 125
        start_y = 230
        step_x = 25
        trace_gap = 60
        trace_height = 25

        for trace_index, (device_id, output_id) in enumerate(
                self.monitors.monitors_dictionary):
            signal_list = self.monitors.monitors_dictionary[(
                device_id, output_id)]
            signal_name = self.devices.get_signal_name(device_id, output_id)

            low_y = start_y - trace_index * trace_gap
            high_y = low_y + trace_height

            GL.glColor3f(0.0, 0.0, 1.0)
            GL.glBegin(GL.GL_LINES)

            previous_y = None
            for i, signal in enumerate(signal_list):
                x = start_x + i * step_x
                x_next = x + step_x

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

                if previous_y is not None and previous_y != y:
                    GL.glVertex2f(x, previous_y)
                    GL.glVertex2f(x, y)

                GL.glVertex2f(x, y)
                GL.glVertex2f(x_next, y)

                previous_y = y

            GL.glEnd()

    def draw_2d_sticky_trace_labels(self):
        """Draw monitor names fixed at the left, aligned with each trace row."""
        size = self.GetClientSize()

        start_y = 230
        trace_gap = 60
        trace_height = 25

        label_x = 10
        label_box_width = 95

        # Switch temporarily to screen coordinates.
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho(0, size.width, 0, size.height, -1, 1)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_LIGHTING)

        for trace_index, (device_id, output_id) in enumerate(
                self.monitors.monitors_dictionary):

            signal_name = self.devices.get_signal_name(device_id, output_id)

            # Original trace y position in world coordinates.
            low_y = start_y - trace_index * trace_gap
            high_y = low_y + trace_height

            # Convert world y position to screen y position.
            screen_low_y = low_y * self.zoom + self.pan_y
            screen_high_y = high_y * self.zoom + self.pan_y

            # If this trace row is vertically off-screen, skip label.
            if screen_high_y < 0 or screen_low_y > size.height:
                continue

            # Draw a small white background strip behind the label.
            GL.glColor3f(1.0, 1.0, 1.0)
            GL.glBegin(GL.GL_QUADS)
            GL.glVertex2f(0, screen_low_y - 5)
            GL.glVertex2f(label_box_width, screen_low_y - 5)
            GL.glVertex2f(label_box_width, screen_high_y + 15)
            GL.glVertex2f(0, screen_high_y + 15)
            GL.glEnd()

            # Draw the label at fixed x but trace-aligned y.
            GL.glColor3f(0.0, 0.0, 0.0)
            self.render_text_overlay(signal_name, label_x, screen_low_y)

            self.render_text_overlay("1", label_x + 70, screen_high_y)
            self.render_text_overlay("0", label_x + 70, screen_low_y)

        GL.glEnable(GL.GL_DEPTH_TEST)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)

    def render_text_overlay(self, text, x_pos, y_pos):
        """Draw text in fixed screen coordinates."""
        GL.glRasterPos2f(x_pos, y_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_12

        for character in text:
            GLUT.glutBitmapCharacter(font, ord(character))

    def draw_cuboid(self, x_pos, z_pos, half_width, half_depth, height):
        """Draw a cuboid at the specified position."""
        GL.glBegin(GL.GL_QUADS)
        GL.glNormal3f(0, -1, 0)
        GL.glVertex3f(x_pos - half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos + half_depth)

        GL.glNormal3f(0, 1, 0)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos + half_depth)

        GL.glNormal3f(-1, 0, 0)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos + half_depth)

        GL.glNormal3f(1, 0, 0)
        GL.glVertex3f(x_pos + half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos + half_depth)

        GL.glNormal3f(0, 0, -1)
        GL.glVertex3f(x_pos - half_width, -6, z_pos - half_depth)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos - half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos - half_depth)

        GL.glNormal3f(0, 0, 1)
        GL.glVertex3f(x_pos - half_width, -6 + height, z_pos + half_depth)
        GL.glVertex3f(x_pos - half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6, z_pos + half_depth)
        GL.glVertex3f(x_pos + half_width, -6 + height, z_pos + half_depth)
        GL.glEnd()

    def draw_monitor_traces_3d(self):
        """Draw all monitored signals as 3D cuboid traces."""
        half_width = 6
        half_depth = 10
        signal_spacing = 45
        cycle_spacing = 22
        high_height = 35
        low_height = 5

        number_of_traces = len(self.monitors.monitors_dictionary)
        centre_offset = (number_of_traces - 1) * signal_spacing / 2

        GL.glColor3f(1.0, 0.7, 0.5)

        for trace_index, (device_id, output_id) in enumerate(
                self.monitors.monitors_dictionary):
            signal_list = self.monitors.monitors_dictionary[(
                device_id, output_id)]
            signal_name = self.devices.get_signal_name(device_id, output_id)
            x_pos = trace_index * signal_spacing - centre_offset

            for cycle_index, signal in enumerate(signal_list):
                z_pos = cycle_index * cycle_spacing

                if signal == self.devices.HIGH:
                    height = high_height
                elif signal == self.devices.RISING:
                    height = high_height
                elif signal == self.devices.LOW:
                    height = low_height
                elif signal == self.devices.FALLING:
                    height = low_height
                else:
                    continue

                self.draw_cuboid(x_pos, z_pos, half_width, half_depth, height)

            GL.glColor3f(1.0, 1.0, 1.0)
            self.render_text_3d(signal_name, x_pos - 10, 0, -35)
            GL.glColor3f(1.0, 0.7, 0.5)

    def render_text_3d(self, text, x_pos, y_pos, z_pos):
        """Draw text in the 3D scene."""
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(x_pos, y_pos, z_pos)
        font = GLUT.GLUT_BITMAP_HELVETICA_10

        for character in text:
            if character == "\n":
                y_pos = y_pos - 20
                GL.glRasterPos3f(x_pos, y_pos, z_pos)
            else:
                GLUT.glutBitmapCharacter(font, ord(character))

        GL.glEnable(GL.GL_LIGHTING)

    def on_paint(self, event):
        """Handle the paint event."""
        wx.PaintDC(self)
        self.render()

    def reset_view(self):
        """Reset pan, zoom and 3D rotation."""
        self.pan_x = 0
        self.pan_y = 0
        self.zoom = 1
        self.scene_rotate = np.identity(4, "f")
        self.init = False
        self.Refresh()

    def on_size(self, event):
        """Handle the canvas resize event."""
        self.init = False
        self.Refresh()

    def on_mouse(self, event):
        """Handle mouse events."""
        if self.trace_mode == "2D":
            self.on_mouse_2d(event)
        else:
            self.on_mouse_3d(event)

    def on_mouse_2d(self, event):
        """Handle mouse events."""
        text = ""
        size = self.GetClientSize()
        ox = (event.GetX() - self.pan_x) / self.zoom
        oy = (size.height - event.GetY() - self.pan_y) / self.zoom
        old_zoom = self.zoom

        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            # Correctly formatted placeholder translation

        if event.Dragging():
            self.pan_x += event.GetX() - self.last_mouse_x
            self.pan_y -= event.GetY() - self.last_mouse_y
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False

        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (event.GetWheelRotation() /
                          (20 * event.GetWheelDelta())))
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = _("Negative mouse wheel rotation. "
                     "Zoom is now: %s") % self.zoom

        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (event.GetWheelRotation() /
                          (20 * event.GetWheelDelta())))
            self.pan_x -= (self.zoom - old_zoom) * ox
            self.pan_y -= (self.zoom - old_zoom) * oy
            self.init = False
            text = _("Positive mouse wheel rotation."
                     " Zoom is now: %s") % self.zoom

        if text:
            self.render(text)
        else:
            self.Refresh()

    def on_mouse_3d(self, event):
        """Handle mouse events."""
        self.SetCurrent(self.context)

        if event.ButtonDown():
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()

        if event.Dragging():
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            x = event.GetX() - self.last_mouse_x
            y = event.GetY() - self.last_mouse_y
            if event.LeftIsDown():
                GL.glRotatef(math.sqrt((x * x) + (y * y)), y, x, 0)
            if event.MiddleIsDown():
                GL.glRotatef((x + y), 0, 0, 1)
            if event.RightIsDown():
                self.pan_x += x
                self.pan_y -= y
            GL.glMultMatrixf(self.scene_rotate)
            GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, self.scene_rotate)
            self.last_mouse_x = event.GetX()
            self.last_mouse_y = event.GetY()
            self.init = False

        if event.GetWheelRotation() < 0:
            self.zoom *= (1.0 + (event.GetWheelRotation() /
                          (20 * event.GetWheelDelta())))
            self.init = False

        if event.GetWheelRotation() > 0:
            self.zoom /= (1.0 - (event.GetWheelRotation() /
                          (20 * event.GetWheelDelta())))
            self.init = False

        self.Refresh()

    def render_text_2d(self, text, x_pos, y_pos):
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
        self.pan_x = -value
        self.init = False
        self.Refresh()

    def set_vertical_scroll(self, value):
        self.pan_y = value
        self.init = False
        self.Refresh()


class Gui(wx.Frame):
    """Configure the main window and all the widgets."""

    def __init__(self, title, path, names, devices, network, monitors):
        """Initialise widgets and layout."""
        super().__init__(parent=None, title=title, size=(800, 600))

        self.path = path
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors

        self.is_running = False
        self.cycles_remaining = 0
        self.cycles_completed = 0

        # Configure the file menu.
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        langMenu = wx.Menu()

        # Define IDs BEFORE appending them
        self.ID_LANG_EN = wx.NewIdRef()
        self.ID_LANG_FR = wx.NewIdRef()
        self.ID_LANG_ZH = wx.NewIdRef()

        # Build the language submenu
        langMenu.Append(self.ID_LANG_EN, "English")
        langMenu.Append(self.ID_LANG_FR, "Français")
        langMenu.Append(self.ID_LANG_ZH, "中文")

        # Assemble the top-level file menu
        fileMenu.Append(wx.ID_ABOUT, _("&About"))
        fileMenu.AppendSubMenu(langMenu, _("&Language"))
        fileMenu.Append(wx.ID_EXIT, _("&Exit"))

        menuBar.Append(fileMenu, _("&File"))
        self.SetMenuBar(menuBar)

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
            style=wx.SL_VERTICAL)
        self.h_scroll = wx.Slider(
            canvas_panel,
            wx.ID_ANY,
            value=0,
            minValue=0,
            maxValue=1000,
            style=wx.SL_HORIZONTAL)

        canvas_row_sizer.Add(self.canvas, 1, wx.EXPAND)
        canvas_row_sizer.Add(self.v_scroll, 0, wx.EXPAND | wx.LEFT, 5)
        canvas_outer_sizer.Add(canvas_row_sizer, 1, wx.EXPAND | wx.ALL, 5)
        canvas_outer_sizer.Add(
            self.h_scroll,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            5)
        canvas_panel.SetSizer(canvas_outer_sizer)

        self.h_scroll.Bind(wx.EVT_SLIDER, self.on_horizontal_scroll)
        self.v_scroll.Bind(wx.EVT_SLIDER, self.on_vertical_scroll)

        terminal_panel = wx.Panel(self)
        terminal_sizer = wx.BoxSizer(wx.VERTICAL)

        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.run_button = wx.Button(terminal_panel, wx.ID_ANY, _("Run"))
        self.continue_button = wx.Button(
            terminal_panel, wx.ID_ANY, _("Continue"))
        self.stop_button = wx.Button(terminal_panel, wx.ID_ANY, _("Stop"))
        self.trace_mode_button = wx.Button(terminal_panel, wx.ID_ANY, _("3D Trace"))
        self.reset_view_button = wx.Button(
            terminal_panel,
            wx.ID_ANY,
            _("Reset View")
        )
        self.add_monitor_button = wx.Button(
            terminal_panel, wx.ID_ANY, _("Add Monitor")
        )
        self.zap_monitor_button = wx.Button(
            terminal_panel, wx.ID_ANY, _("Zap Monitor")
        )
        

        toolbar_sizer.Add(self.run_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.continue_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.stop_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.add_monitor_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.zap_monitor_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.trace_mode_button, 0, wx.RIGHT, 5)
        toolbar_sizer.Add(self.reset_view_button, 0, wx.RIGHT, 5)

        self.output_box = wx.TextCtrl(
            terminal_panel,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.switch_box = wx.TextCtrl(
            terminal_panel,
            wx.ID_ANY,
            "",
            style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.switch_button_panel = wx.ScrolledWindow(
            terminal_panel,
            wx.ID_ANY,
            style=wx.VSCROLL
        )
        self.switch_button_panel.SetScrollRate(0, 10)

        self.switch_button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.switch_button_panel.SetSizer(self.switch_button_sizer)

        self.switch_buttons = {}

        self.switch_buttons = {}
        self.text_box = wx.TextCtrl(
            terminal_panel,
            wx.ID_ANY,
            "",
            style=wx.TE_PROCESS_ENTER)

        terminal_sizer.Add(toolbar_sizer, 0, wx.EXPAND | wx.ALL, 5)

        info_output_sizer = wx.BoxSizer(wx.HORIZONTAL)

        switch_area_sizer = wx.BoxSizer(wx.HORIZONTAL)
        switch_area_sizer.Add(self.switch_box, 1, wx.EXPAND | wx.RIGHT, 5)
        switch_area_sizer.Add(self.switch_button_panel, 0, wx.EXPAND)

        info_output_sizer.Add(self.output_box, 2, wx.EXPAND | wx.RIGHT, 5)
        info_output_sizer.Add(switch_area_sizer, 1, wx.EXPAND)

        terminal_sizer.Add(info_output_sizer, 1, wx.EXPAND |
                           wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        terminal_sizer.Add(self.text_box, 0, wx.EXPAND |
                           wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        terminal_panel.SetSizer(terminal_sizer)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(canvas_panel, 2, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(terminal_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.Bind(wx.EVT_MENU, self.on_menu)
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_button)
        self.continue_button.Bind(wx.EVT_BUTTON, self.on_continue_button)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_button)
        self.add_monitor_button.Bind(
            wx.EVT_BUTTON, self.on_add_monitor_button
        )
        self.zap_monitor_button.Bind(
            wx.EVT_BUTTON, self.on_zap_monitor_button
        )
        self.reset_view_button.Bind(wx.EVT_BUTTON, self.on_reset_view_button)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_box)
        self.trace_mode_button.Bind(wx.EVT_BUTTON, self.on_trace_mode_button)
        self.h_scroll.Bind(wx.EVT_SLIDER, self.on_horizontal_scroll)
        self.v_scroll.Bind(wx.EVT_SLIDER, self.on_vertical_scroll)

        self.SetSizeHints(600, 600)
        self.SetSizer(main_sizer)
        self.Layout()

        self.write_output(_("Ready. Type h for help"))
        self.update_switch_box()
        self.build_switch_buttons()
        self.update_switch_buttons()

    def on_menu(self, event):
        """Handle the event when the user selects a menu item."""
        Id = event.GetId()
        if Id == wx.ID_EXIT:
            self.Close(True)
        elif Id == wx.ID_ABOUT:
            message = _(
                "Logic Simulator designed by group 14\n"
                "Definition file used: %s") % str(self.path)
            wx.MessageBox(
                message,
                _("About Logsim"),
                wx.ICON_INFORMATION | wx.OK)
        elif Id == self.ID_LANG_EN.GetId():
            self.change_language("en")
        elif Id == self.ID_LANG_FR.GetId():
            self.change_language("fr")
        elif Id == self.ID_LANG_ZH.GetId():
            self.change_language("zh_CN")

    def change_language(self, lang_code):
        with open("lang_pref.txt", "w") as f:
            f.write(lang_code)

        wx.MessageBox(
            _("Language changed. "
              "Please restart the application to apply changes."),
            _("Restart Required"),
            wx.ICON_INFORMATION | wx.OK)

    def on_run_button(self, event):
        """Handle the event when the user clicks the run button."""
        text = self.text_box.GetValue().strip()
        if not text:
            command = "r 20"
        elif text.isdigit():
            command = "r " + text
        else:
            command = text
        self.process_command(command)
        self.text_box.Clear()

    def on_continue_button(self, event):
        """Handle the event when the user clicks the continue button."""
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
        self.write_output(_("Simulation stopped by user."))
        self.canvas.render(_("Simulation stopped."))

    def on_add_monitor_button(self, event):
        """Add a monitor using the signal name in the text box."""
        signal_name = self.text_box.GetValue().strip()

        if not signal_name:
            self.write_output(_("Error: enter a signal name to monitor."))
            return

        command = "m " + signal_name
        self.process_command(command)
        self.text_box.Clear()

    def on_zap_monitor_button(self, event):
        """Remove a monitor using the signal name in the text box."""
        signal_name = self.text_box.GetValue().strip()

        if not signal_name:
            self.write_output(_("Error: enter a signal name to remove."))
            return

        command = "z " + signal_name
        self.process_command(command)
        self.text_box.Clear()

    def on_reset_view_button(self, event):
        """Reset the canvas pan, zoom and 3D rotation."""
        self.canvas.reset_view()
        self.write_output(_("Canvas view reset."))

    def on_text_box(self, event):
        """Handle the event when the user enters text in the terminal box."""
        command = self.text_box.GetValue().strip()
        self.process_command(command)
        self.text_box.Clear()

    def on_trace_mode_button(self, event):
        """Switch between 2D and 3D signal trace views."""
        if self.canvas.trace_mode == "2D":
            self.canvas.trace_mode = "3D"
            self.trace_mode_button.SetLabel(_("2D Trace"))
            self.write_output(_("Switched to 3D trace view."))
        else:
            self.canvas.trace_mode = "2D"
            self.trace_mode_button.SetLabel(_("3D Trace"))
            self.write_output(_("Switched to 2D trace view."))
        self.canvas.init = False
        self.canvas.Refresh()

    def update_switch_box(self):
        """Refresh value in the switch box."""
        switch_text = _("Switch values:\n")
        for device_id in self.devices.find_devices():
            device = self.devices.get_device(device_id)
            if device.device_kind == self.devices.SWITCH:
                switch_name = self.names.get_name_string(device_id)
                switch_value = device.switch_state
                switch_text += "%s = %s\n" % (switch_name, switch_value)
        self.switch_box.SetValue(switch_text)

    def build_switch_buttons(self):
        """Create one toggle button for each switch."""
        self.switch_button_sizer.Clear(delete_windows=True)
        self.switch_buttons = {}

        for device_id in self.devices.find_devices():
            device = self.devices.get_device(device_id)

            if device.device_kind == self.devices.SWITCH:
                switch_name = self.names.get_name_string(device_id)
                button = wx.Button(
                    self.switch_button_panel,
                    wx.ID_ANY,
                    "Toggle " + switch_name
                )

                button.Bind(
                    wx.EVT_BUTTON,
                    lambda event, sid=device_id: self.on_switch_toggle_button(
                        event, sid
                    )
                )

                self.switch_button_sizer.Add(
                    button,
                    0,
                    wx.EXPAND | wx.BOTTOM,
                    3
                )

                self.switch_buttons[device_id] = button

        self.switch_button_panel.Layout()
        self.switch_button_panel.FitInside()
        self.update_switch_buttons()

    def on_switch_toggle_button(self, event, switch_id):
        """Toggle the value of a switch button."""
        device = self.devices.get_device(switch_id)
        switch_name = self.names.get_name_string(switch_id)

        if device.switch_state == 0:
            new_value = 1
        else:
            new_value = 0

        self.devices.set_switch(switch_id, new_value)

        self.write_output(
    _("Set switch %s to %s.") % (switch_name, new_value))

        self.update_switch_box()
        self.update_switch_buttons()
        self.canvas.render(
            _("Set switch %s to %s.") % (switch_name, new_value)
        )

    def update_switch_buttons(self):
        """Refresh switch button labels."""
        for switch_id, button in self.switch_buttons.items():
            device = self.devices.get_device(switch_id)
            switch_name = self.names.get_name_string(switch_id)

            if device.switch_state == 0:
                button.SetLabel(switch_name + ": 0 → 1")
            else:
                button.SetLabel(switch_name + ": 1 → 0")

    def update_scrollbars(self):
        """Update scrollbar ranges from monitor count and trace length."""
        step_x = 25
        trace_gap = 60
        canvas_size = self.canvas.GetClientSize()
        total_width = self.cycles_completed * step_x + 125
        total_height = len(self.monitors.monitors_dictionary) * trace_gap + 100
        max_horizontal_scroll = max(0, total_width - canvas_size.width)
        max_vertical_scroll = max(0, total_height - canvas_size.height)
        self.h_scroll.SetRange(0, max_horizontal_scroll)
        self.v_scroll.SetRange(0, max_vertical_scroll)

    def process_command(self, command):
        """Interpret a terminal command and call the appropriate method."""
        if not command:
            self.write_output(_("Error: no command entered."))
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
                _("The run button run simulation for 20 cycles.\n"
                  "The continue button runs a further 10 cycles.\n"
                  "Command list:\n"
                  "Run for N cycles: r N\n"
                  "Continue for N cycles: c N\n"
                  "Set the value of switch N: s SWN 1 or s SWN 0\n"
                  "Add a monitor on Gate N: m GN\n"
                  "Remove a monitor on Gate N: z GN\n"
                  "Press the stop button to quit the simulation\n")
            )
        else:
            self.write_output(_("Error: unknown command '%s'.") % command_type)

    def handle_run_command(self, parts):
        cycles = self.get_cycle_argument(parts, "r N")
        if cycles is None:
            return
        self.start_simulation(cycles, cold_start=True)
        self.update_scrollbars()
        self.canvas.Refresh()

    def handle_continue_command(self, parts):
        cycles = self.get_cycle_argument(parts, "c N")
        if cycles is None:
            return
        self.start_simulation(cycles, cold_start=False)

    def handle_switch_command(self, parts):
        if len(parts) != 3:
            self.write_output(_("Error: usage is s X N, for example s SW1 1."))
            return
        switch_name = parts[1]
        try:
            switch_value = int(parts[2])
        except ValueError:
            self.write_output(_("Error: switch value must be 0 or 1."))
            return
        if switch_value not in [0, 1]:
            self.write_output(_("Error: switch value must be 0 or 1."))
            return

        self.do_set_switch(switch_name, switch_value)
        self.canvas.render(
            _("Switch %s set to %s.") %
            (switch_name, switch_value))
        self.update_switch_box()
        self.update_switch_buttons()

    def handle_monitor_command(self, parts):
        if len(parts) != 2:
            self.write_output(_("Error: usage is m X, for example m G1."))
            return
        signal_name = parts[1]
        device_id, output_id = self.devices.get_signal_ids(signal_name)
        if device_id is None:
            return

        error_type = self.monitors.make_monitor(
            device_id, output_id, self.cycles_completed)
        if error_type == self.monitors.NO_ERROR:
            self.do_add_monitor(signal_name)
        elif error_type == self.monitors.MONITOR_PRESENT:
            self.write_output(_("Monitor on %s already exists.") % signal_name)
        elif error_type == self.monitors.NOT_OUTPUT:
            self.write_output(_("%s is not an output.") % signal_name)
        elif error_type == self.network.DEVICE_ABSENT:
            self.write_output(_("%s is not defined.") % signal_name)
        else:
            self.write_output(_("Could not add monitor on %s.") % signal_name)

        self.update_scrollbars()
        self.canvas.Refresh()

    def handle_zap_command(self, parts):
        if len(parts) != 2:
            self.write_output(_("Error: usage is z X, for example z G1."))
            return

        signal_name = parts[1]
        if "." in signal_name:
            device_name, output_name = signal_name.split(".", 1)
        else:
            device_name, output_name = signal_name, None

        device_id = self.names.query(device_name)
        if device_name is None:
            self.write_output(
                _("Error: device '%s' is not defined.") %
                device_name)
            return

        if output_name is not None:
            output_id = self.names.query(output_name)
            if output_id is None:
                self.write_output(
                    _("Error: output '%s' is not defined.") %
                    output_name)
                return

        device_id, output_id = self.devices.get_signal_ids(signal_name)
        device = self.devices.get_device(device_id)

        if device is None:
            self.write_output(
                _("Error: device '%s' is not in the network.") %
                device_name)
            return
        if output_id not in device.outputs:
            self.write_output(
                _("Error: signal '%s' is not an output.") %
                signal_name)
            return
        if (device_id, output_id) not in self.monitors.monitors_dictionary:
            self.write_output(
                _("Error: no monitor exists on signal '%s'.") %
                signal_name)
            return

        self.monitors.remove_monitor(device_id, output_id)
        self.write_output(_("Monitor removed: %s") % signal_name)
        self.update_scrollbars()
        self.canvas.Refresh()

    def handle_help_command(self, parts):
        cycles = self.get_cycle_argument(parts, "h")
        if cycles is None:
            return

    def get_cycle_argument(self, parts, usage):
        if len(parts) != 2:
            self.write_output(_("Error: usage is %s.") % usage)
            return None
        try:
            cycles = int(parts[1])
        except ValueError:
            self.write_output(_("Error: number of cycles must be an integer."))
            return None
        if cycles <= 0:
            self.write_output(_("Error: number of cycles must be positive."))
            return None
        return cycles

    def start_simulation(self, cycles, cold_start=False):
        if self.is_running:
            self.write_output(_("Error: simulation is already running."))
            return
        if cold_start:
            self.do_prepare_fresh_run()
            self.cycles_completed = 0

        self.cycles_remaining = cycles
        self.is_running = True
        self.write_output(_("Running for %s cycle(s).") % cycles)
        self.update_scrollbars()
        self.canvas.Refresh()
        self.run_next_cycle()

    def run_next_cycle(self):
        if not self.is_running:
            return

        if self.cycles_remaining <= 0:
            self.is_running = False
            self.write_output(_("Simulation finished."))
            self.canvas.render(
                _("Simulation finished after %s cycle(s).") %
                self.cycles_completed)
            return

        success = self.do_one_simulation_cycle()
        if not success:
            self.is_running = False
            self.write_output(
                _("Error: simulation failed to reach steady state."))
            self.canvas.render(_("Simulation error."))
            return

        self.cycles_remaining -= 1
        self.cycles_completed += 1
        self.canvas.render(_("Cycle %s") % self.cycles_completed)
        wx.CallLater(50, self.run_next_cycle)
        self.update_scrollbars()
        self.canvas.Refresh()

    def do_prepare_fresh_run(self):
        self.monitors.reset_monitors()
        self.devices.cold_startup()

    def do_one_simulation_cycle(self):
        success = self.network.execute_network(self.cycles_completed)
        if success:
            self.monitors.record_signals()
        return success

    def do_set_switch(self, switch_name, switch_value):
        switch_id = self.names.query(switch_name)
        if switch_id is None:
            self.write_output(_("Error: unknown switch %s.") % switch_name)
            return
        self.devices.set_switch(switch_id, switch_value)
        self.write_output(
            _("Set switch %s to %s.") %
            (switch_name, switch_value))
        self.update_switch_buttons

    def do_add_monitor(self, signal_name):
        device_id, output_id = self.devices.get_signal_ids(signal_name)
        self.monitors.make_monitor(device_id, output_id)
        self.write_output(_("Added monitor on %s.") % signal_name)

    def do_remove_monitor(self, signal_name):
        device_id, output_id = self.devices.get_signal_ids(signal_name)
        self.monitors.remove_monitor(device_id, output_id)
        self.write_output(_("Removed monitor from %s.") % signal_name)

    def on_horizontal_scroll(self, event):
        value = self.h_scroll.GetValue()
        self.canvas.set_horizontal_scroll(value)

    def on_vertical_scroll(self, event):
        value = self.v_scroll.GetValue()
        self.canvas.set_vertical_scroll(value)

    def write_output(self, message):
        self.output_box.AppendText(message + "\n")


if __name__ == "__main__":
    app = wx.App()

    lang_pref = "en"
    if os.path.exists("lang_pref.txt"):
        with open("lang_pref.txt", "r") as f:
            lang_pref = f.read().strip()

    if lang_pref == "fr":
        wx_lang = wx.LANGUAGE_FRENCH
    elif lang_pref == "zh_CN":
        wx_lang = wx.LANGUAGE_CHINESE_SIMPLIFIED
    else:
        wx_lang = wx.LANGUAGE_ENGLISH

    locale = wx.Locale(wx_lang)
    locale.AddCatalogLookupPathPrefix('locale')
    locale.AddCatalog('logsim')

    gui = Gui(
        "Logic Simulator GUI Test",
        path=None,
        names=None,
        devices=None,
        network=None,
        monitors=None)
    gui.Show()
    app.MainLoop()
