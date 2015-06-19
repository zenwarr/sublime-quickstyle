import sublime, sublime_plugin
import string

whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_-'
style_extensions = ['css', 'sass', 'scss', 'styl', 'less']
stylus_use_indented = True

class QsAddRuleCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    self.cur_pos = self.view.sel()[0].a
    class_name = self.get_class_nane()
    if len(class_name) == 0:
      sublime.error_message('No valid css class at this point')
      return

    target_view = self.find_target_view()
    if target_view == None:
      sublime.error_message('No open style file found')
      return

    sublime.active_window().focus_view(target_view)

    generator = QsRuleGenerator(target_view)
    generated_rule = generator.generate(target_view.sel()[0].a, class_name)
    if generated_rule == None or len(generated_rule) == 0:
      sublime.error_message('Error while generating rule')
      return

    generator.insert(edit, target_view.sel()[0].a, generated_rule)

  def get_class_nane(self):
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
      file_name = view.file_name()
      for ext in style_extensions:
        if file_name.endswith('.' + ext):
          return view

class QsRuleGenerator:
  def __init__(self, view):
    self.view = view

    view_settings = self.view.settings()
    self.tabWidth = view_settings.get('tab_size')
    self.useTabs = not view_settings.get('translate_tabs_to_spaces')

  def detect_syntax(self, point):
    scopes = self.view.scope_name(point).split(' ')
    for scope in scopes:
      if scope == 'source.stylus':
        return 'stylus-indented' if stylus_use_indented else 'stylus'
      elif scope == 'source.scss':
        return 'scss'
      elif scope == 'source.sass':
        return 'sass'
      elif scope == 'source.less':
        return 'less'
      elif scope == 'source.css':
        return 'css'
    return None

  def detect_indentation_prefix(self, point):
    line = self.view.line(point)
    line_text = self.view.substr(line)

    indent = ''
    for char in line_text:
      if char in ' \t':
        indent += char

    return indent

  def get_indentation(self):
    if self.useTabs:
      return '\t'
    else:
      return ' ' * self.tabWidth

  def concat(self, indentation, lines):
    return '\n'.join([lines[0]] + [indentation + line for line in lines[1:]])

  def generate(self, point, class_name):
    syntax = self.detect_syntax(point)
    if syntax == None:
      sublime.error_message('Unsupported syntax in target file')
      return

    indentation = self.detect_indentation_prefix(point)

    if syntax in ['css', 'scss', 'stylus', 'less']:
      return self.concat(indentation, [
               '.' + class_name + ' {',
               self.get_indentation() + '$',
               '}'
                ]) + ('' if len(indentation) else '\n')
    elif syntax in ['sass', 'stylus-indented']:
      return self.concat(indentation, [
                '.' + class_name,
                self.get_indentation() + '$'
                ]) + ('' if len(indentation) else '\n')
    else:
      raise Error()

  def insert(self, edit, point, generated):
    if generated == None or len(generated) == 0:
      return

    # find where we should place cursor after inserting, this position is indicated by $ sign
    cursor_offset = generated.find('$')
    if cursor_offset < 0:
      cursor_offset = len(generated)

    # now remove $ sign from generated string and insert it into view
    generated = generated[:cursor_offset] + generated[cursor_offset+1:]
    self.view.insert(edit, point, generated)

    # locate cursor at the insertion point
    cursor_region = sublime.Region(point + cursor_offset)
    self.view.sel().clear()
    self.view.sel().add(cursor_region)
    self.view.show(cursor_region)


def plugin_loaded():
  global stylus_use_indented

  qs_settings = sublime.load_settings('quickstyle.sublime-settings')
  stylus_use_indented = qs_settings.get('stylus_use_indented', True)