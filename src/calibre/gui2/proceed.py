#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2012, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

from collections import namedtuple

from PyQt5.Qt import (
    QWidget, Qt, QLabel, QVBoxLayout, QPixmap, QDialogButtonBox, QApplication,
    QSize, pyqtSignal, QIcon, QPlainTextEdit, QCheckBox, QPainter, QHBoxLayout,
    QPainterPath, QRectF)

from calibre.constants import __version__
from calibre.gui2.dialogs.message_box import ViewLog

Question = namedtuple('Question', 'payload callback cancel_callback '
        'title msg html_log log_viewer_title log_is_file det_msg '
        'show_copy_button checkbox_msg checkbox_checked action_callback '
        'action_label action_icon focus_action show_det show_ok')

class ProceedQuestion(QWidget):

    ask_question = pyqtSignal(object, object, object)

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setVisible(False)

        self.questions = []

        self.icon_label = ic = QLabel(self)
        ic.setPixmap(QPixmap(I('dialog_question.png')))
        self.msg_label = msg = QLabel('some random filler text')
        msg.setWordWrap(True)
        ic.setMaximumSize(QSize(64, 64))
        ic.setScaledContents(True)
        self.bb = QDialogButtonBox()
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        self.log_button = self.bb.addButton(_('View log'), self.bb.ActionRole)
        self.log_button.setIcon(QIcon(I('debug.png')))
        self.log_button.clicked.connect(self.show_log)
        self.copy_button = self.bb.addButton(_('&Copy to clipboard'),
                self.bb.ActionRole)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.action_button = self.bb.addButton('', self.bb.ActionRole)
        self.action_button.clicked.connect(self.action_clicked)
        self.show_det_msg = _('Show &details')
        self.hide_det_msg = _('Hide &details')
        self.det_msg_toggle = self.bb.addButton(self.show_det_msg, self.bb.ActionRole)
        self.det_msg_toggle.clicked.connect(self.toggle_det_msg)
        self.det_msg_toggle.setToolTip(
                _('Show detailed information about this error'))
        self.det_msg = QPlainTextEdit(self)
        self.det_msg.setReadOnly(True)
        self.bb.setStandardButtons(self.bb.Yes|self.bb.No|self.bb.Ok)
        self.bb.button(self.bb.Yes).setDefault(True)
        self.title_label = title = QLabel('A dummy title')
        f = title.font()
        f.setBold(True)
        title.setFont(f)

        self.checkbox = QCheckBox('', self)

        self._l = l = QVBoxLayout(self)
        self._h = h = QHBoxLayout()
        self._v = v = QVBoxLayout()
        v.addWidget(title), v.addWidget(msg)
        h.addWidget(ic), h.addSpacing(10), h.addLayout(v), l.addLayout(h)
        l.addSpacing(5)
        l.addWidget(self.checkbox)
        l.addWidget(self.det_msg)
        l.addWidget(self.bb)

        self.ask_question.connect(self.do_ask_question,
                type=Qt.QueuedConnection)
        self.setFocusPolicy(Qt.NoFocus)
        for child in self.findChildren(QWidget):
            child.setFocusPolicy(Qt.NoFocus)
        self.setFocusProxy(self.parent())

    def copy_to_clipboard(self, *args):
        QApplication.clipboard().setText(
                'calibre, version %s\n%s: %s\n\n%s' %
                (__version__, unicode(self.windowTitle()),
                    unicode(self.msg_label.text()),
                    unicode(self.det_msg.toPlainText())))
        self.copy_button.setText(_('Copied'))

    def action_clicked(self):
        if self.questions:
            q = self.questions[0]
            self.questions[0] = q._replace(callback=q.action_callback)
        self.accept()

    def accept(self):
        if self.questions:
            payload, callback, cancel_callback = self.questions[0][:3]
            self.questions = self.questions[1:]
            cb = None
            if self.checkbox.isVisible():
                cb = bool(self.checkbox.isChecked())
            self.ask_question.emit(callback, payload, cb)
        self.hide()

    def reject(self):
        if self.questions:
            payload, callback, cancel_callback = self.questions[0][:3]
            self.questions = self.questions[1:]
            cb = None
            if self.checkbox.isVisible():
                cb = bool(self.checkbox.isChecked())
            self.ask_question.emit(cancel_callback, payload, cb)
        self.hide()

    def do_ask_question(self, callback, payload, checkbox_checked):
        if callable(callback):
            args = [payload]
            if checkbox_checked is not None:
                args.append(checkbox_checked)
            callback(*args)
        self.show_question()

    def toggle_det_msg(self, *args):
        vis = unicode(self.det_msg_toggle.text()) == self.hide_det_msg
        self.det_msg_toggle.setText(self.show_det_msg if vis else
                self.hide_det_msg)
        self.det_msg.setVisible(not vis)
        self.do_resize()

    def do_resize(self):
        sz = self.sizeHint() + QSize(100, 0)
        sz.setWidth(min(500, sz.width()))
        sz.setHeight(min(500, sz.height()))
        self.resize(sz)
        self.position_widget()

    def show_question(self):
        if self.isVisible():
            self.raise_()
            return
        if self.questions:
            question = self.questions[0]
            self.msg_label.setText(question.msg)
            self.title_label.setText(question.title)
            self.log_button.setVisible(bool(question.html_log))
            self.copy_button.setText(_('&Copy to clipboard'))
            self.copy_button.setVisible(bool(question.show_copy_button))
            self.action_button.setVisible(question.action_callback is not None)
            if question.action_callback is not None:
                self.action_button.setText(question.action_label or '')
                self.action_button.setIcon(
                    QIcon() if question.action_icon is None else question.action_icon)
            self.det_msg.setPlainText(question.det_msg or '')
            self.det_msg.setVisible(False)
            self.det_msg_toggle.setVisible(bool(question.det_msg))
            self.det_msg_toggle.setText(self.show_det_msg)
            self.checkbox.setVisible(question.checkbox_msg is not None)
            if question.checkbox_msg is not None:
                self.checkbox.setText(question.checkbox_msg)
                self.checkbox.setChecked(question.checkbox_checked)
            self.bb.button(self.bb.Ok).setVisible(question.show_ok)
            self.bb.button(self.bb.Yes).setVisible(not question.show_ok)
            self.bb.button(self.bb.No).setVisible(not question.show_ok)
            if question.show_det:
                self.toggle_det_msg()
            else:
                self.do_resize()
            self.show_widget()
            button = self.action_button if question.focus_action and question.action_callback is not None else \
                (self.bb.button(self.bb.Ok) if question.show_ok else self.bb.button(self.bb.Yes))
            button.setDefault(True)
            self.raise_()

    def position_widget(self):
        geom = self.parent().geometry()
        x = geom.right() - self.width()
        sb = self.parent().statusBar()
        if sb is None:
            y = geom.bottom() - self.height()
        else:
            y = sb.geometry().top() - self.height()
        self.move(x, y)

    def show_widget(self):
        self.show()
        self.position_widget()

    def dummy_question(self):
        self(lambda *args:args, (), 'dummy log', 'Log Viewer', 'A Dummy Popup',
             'This is a dummy popup to easily test things, with a long line of text that should wrap',
             checkbox_msg='A dummy checkbox',
             action_callback=lambda *args: args, action_label='An action')

    def __call__(self, callback, payload, html_log, log_viewer_title, title,
            msg, det_msg='', show_copy_button=False, cancel_callback=None,
            log_is_file=False, checkbox_msg=None, checkbox_checked=False,
            action_callback=None, action_label=None, action_icon=None, focus_action=False,
            show_det=False, show_ok=False, **kw):
        '''
        A non modal popup that notifies the user that a background task has
        been completed. This class guarantees that only a single popup is
        visible at any one time. Other requests are queued and displayed after
        the user dismisses the current popup.

        :param callback: A callable that is called with payload if the user
        asks to proceed. Note that this is always called in the GUI thread.
        :param cancel_callback: A callable that is called with the payload if
        the users asks not to proceed.
        :param payload: Arbitrary object, passed to callback
        :param html_log: An HTML or plain text log
        :param log_viewer_title: The title for the log viewer window
        :param title: The title for this popup
        :param msg: The msg to display
        :param det_msg: Detailed message
        :param log_is_file: If True the html_log parameter is interpreted as
                            the path to a file on disk containing the log
                            encoded with utf-8
        :param checkbox_msg: If not None, a checkbox is displayed in the
                             dialog, showing this message. The callback is
                             called with both the payload and the state of the
                             checkbox as arguments.
        :param checkbox_checked: If True the checkbox is checked by default.
        :param action_callback: If not None, an extra button is added, which
                                when clicked will cause action_callback to be called
                                instead of callback. action_callback is called in
                                exactly the same way as callback.
        :param action_label: The text on the action button
        :param action_icon: The icon for the action button, must be a QIcon object or None
        :param focus_action: If True, the action button will be focused instead of the Yes button
        :param show_det: If True, the Detailed message will be shown initially
        :param show_ok: If True, OK will be shown instead of YES/NO
        '''
        question = Question(
            payload, callback, cancel_callback, title, msg, html_log,
            log_viewer_title, log_is_file, det_msg, show_copy_button,
            checkbox_msg, checkbox_checked, action_callback, action_label,
            action_icon, focus_action, show_det, show_ok)
        self.questions.append(question)
        self.show_question()

    def show_log(self):
        if self.questions:
            q = self.questions[0]
            log = q.html_log
            if q.log_is_file:
                with open(log, 'rb') as f:
                    log = f.read().decode('utf-8')
            self.log_viewer = ViewLog(q.log_viewer_title, log,
                        parent=self)

    def paintEvent(self, ev):
        br = 12  # border_radius
        bw = 1  # border_width
        pal = self.palette()
        c = pal.color(pal.Window)
        c.setAlphaF(0.86)
        p = QPainterPath()
        p.addRoundedRect(QRectF(self.rect()), br, br)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillPath(p, c)
        p.addRoundedRect(QRectF(self.rect()).adjusted(bw, bw, -bw, -bw), br, br)
        painter.fillPath(p, pal.color(pal.WindowText))
        painter.end()

def main():
    from calibre.gui2 import Application
    from PyQt5.Qt import QMainWindow, QStatusBar, QTimer
    app = Application([])
    w = QMainWindow()
    s = QStatusBar(w)
    w.setStatusBar(s)
    s.showMessage('Testing ProceedQuestion')
    w.show()
    p = ProceedQuestion(w)
    def doit():
        p.dummy_question()
        p(lambda p:None, None, 'ass2', 'ass2', 'testing2', 'testing2',
                det_msg='details shown first', show_det=True, show_ok=True)
    QTimer.singleShot(10, doit)
    app.exec_()

if __name__ == '__main__':
    main()

