import sublime, sublime_plugin
import string

whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_-'

class QsAddRuleCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.cur_pos = self.view.sel()[0].a
    class_or_id_name = self.get_class_or_id()
    if len(class_or_id_name) == 0:
      sublime.error_message('No valid css class at this point')
      return

    target_view = self.find_target_view()
    if target_view == None:
      sublime.error_message('No open css file found')
      return

    sublime.active_window().focus_view(target_view)

    target_sel = target_view.sel()[0]
    target_sel_start = target_sel.a

    gen_rule = '.{0} {{\n  \n}}'.format(class_or_id_name)
    target_view.insert(edit, target_sel_start, gen_rule)

    cursor_region = sublime.Region(target_sel_start + len(gen_rule) - 2)

    target_view.sel().clear()
    target_view.sel().add(cursor_region)

    target_view.show(cursor_region)

  def get_class_or_id(self):
    line = self.view.line(self.cur_pos)
    line_text = self.view.substr(line)
    if line_text == None:
      return ''

    result_class = ''

    # find start of class
    cur_line_pos = self.cur_pos - line.a
    if cur_line_pos < 0 or cur_line_pos >= len(line_text):
      return ''
    cur_char = line_text[cur_line_pos]
    while cur_char in whitelist:
      result_class = cur_char + result_class
      if cur_line_pos <= 0:
        break
      cur_line_pos -= 1
      cur_char = line_text[cur_line_pos]

    # find end of class
    cur_line_pos = self.cur_pos - line.a + 1
    cur_char = line_text[cur_line_pos]
    while cur_char in whitelist:
      result_class = result_class + cur_char
      if cur_line_pos >= len(line_text):
        break
      cur_line_pos += 1
      cur_char = line_text[cur_line_pos]

    return result_class

  def find_target_view(self):
    win = sublime.active_window()
    all_views = win.views()

    for view in all_views:
      if view.file_name().endswith('.css'):
        return view