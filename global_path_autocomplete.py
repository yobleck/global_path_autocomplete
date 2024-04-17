import os
import re
import time

import sublime
import sublime_plugin


class GlobalPathAutocomplete(sublime_plugin.EventListener):
    # def on_activated(self, view):
    #     print("test load")
    #     settings = view.settings().get("auto_complete_triggers")
    #     settings += {"characters": "/", "selector": "text.*"}
    #     view.settings().set("auto_complete_triggers", settings)

    def on_query_completions(self, view, prefix, locations):
        start = time.time()
        # TODO handle spaces in file names breaking the actual placement of text
        # TODO handle restricted folders
        # TODO handle "../"
        # TODO regex doesn't work if it starts on the first 2 chars of a line
        # re implement more robust "./", "../" and "~/" handling

        out: list = []
        args: int = 0  # tries to remove extra options from the completion menu

        # causes auto complete to trigger on "/" TODO move to on_load or on_activated?
        # might cause issues with suggestions showing up when they shouldn't
        settings = view.settings().get("auto_complete_triggers")
        # TODO strict auto_complete_preserve_order
        settings += {"characters": "/", "selector": "text.*"}
        view.settings().set("auto_complete_triggers", settings)

        # print(locations)
        if len(locations) == 1:  # handle no cursor or multi cursor
            cursor = locations[0]

            # scan through characters to get current line up to cursor
            x: int = 1
            while (current_line := view.substr(sublime.Region(cursor, cursor - x)))[0] not in ["\n"]:
                if x > 4096:  # Linux max file path length. If more loops than this, then something is wrong
                    print("This shouldn't happen :O")
                    break
                x += 1

            # print("current line:", current_line)
            # old regex  [\.|~]*/[\w/\s\-\.]*     (?:\.{1,2}|~)?/[\w/\s\-\.]*
            re_list: list = re.findall(r'.{2}/[\w/\s\-\.]*', current_line)  # regex match all file paths
            # print("re match:", re_list)
            re_match: str = ""  # TODO replace with re_list[-1]?
            original_path: str = ""
            expanded_path: str = ""
            # is_expanded: bool = False
            if re_list:  # get last match if it exists
                re_match = re_list[-1]
            print("re_match", re_match)

            if re_match and current_line.endswith(re_match):  # don't grab regex earlier in line
                # print("end", current_line, re_match)
                if re_match[1:2] == ".":  # handle folder that current file is in
                    # print("test", os.path.split(view.file_name())[0])
                    expanded_path = os.path.split(view.file_name())[0] + re_match[2:]
                    original_path = re_match[1:]
                    # is_expanded = True
                elif re_match[1:2] == "~":  # handle user home folder
                    expanded_path = os.path.expanduser("~") + re_match[2:]
                    original_path = re_match[1:]
                    # is_expanded = True
                elif re_match[0:2] == "..":  # TODO handle folder above current
                    expanded_path = ""
                else:
                    expanded_path = re_match[2:]
                    original_path = re_match[2:]
                # print("orig", original_path)
                # print("exp", expanded_path)

                head, tail = os.path.split(expanded_path)
                # print("h t", head, tail)
                if os.path.isdir(head):
                    for f in os.listdir(head):
                        if f.startswith(tail):
                            if head[-1] != "/":  # handles /hhome issue
                                head += "/"
                            if os.path.isdir(head + f):  # check if item is file or dir
                                a = "directory"
                                k = (sublime.KIND_ID_COLOR_BLUISH, "d", "directory")
                            else:
                                a = "file"
                                k = (sublime.KIND_ID_COLOR_GREENISH, "f", "file")
                            # print("comp", (original_path if is_expanded else head), f)
                            # (original_path if is_expanded else head) + f,
                            out.append(sublime.CompletionItem(trigger=original_path[:-len(tail)] + f,
                                                              # replaced by removesuffix in python 3.9+
                                                              completion=original_path[:-len(tail)] + f,
                                                              annotation=a,
                                                              kind=k
                                                              )
                                       )
                    out.sort(key=lambda x: x.completion.upper())
                    # print("############################")
                    # for o in out:
                    #     print(o.completion)
                    args = 24  # sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

            # print("out", out[:12])
            # print("time:", time.time() - start)
            return (out, args)
