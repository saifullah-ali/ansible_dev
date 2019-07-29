# (c) 2019, Ansible Development Project
# Saifullah Bin Ali, saifullah.ali009@hotmail.
# https://github.com/saifullah-ali
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# This action module is developed upon telnet module. System where we get Unicode GUI after doing telnet
# can use this module/plugins. This will enable user to bypass the GUI and put them in bynary CLI prompts
# where they can execute their commands one-by-one and also see the out-put.
# Example in playbook:
#   - name: run show commands
#     gui_telnet:
#        host: "{{ ip_address }}"
#        user: admin
#        password: admin
#        login_prompt: "Enter User Name: "
#        password_prompt: "Enter Password: "
#        command:
#          - version
#    register: results
#  - debug: msg="{{ results.cli_result }}"

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import telnetlib
from time import sleep

from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.six import text_type
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
import re

display = Display()


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        if self._task.environment and any(self._task.environment):
            self._display.warning('The telnet task does not support the environment keyword')

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if self._play_context.check_mode:
            # in --check mode, always skip this module execution
            result['skipped'] = True
            result['msg'] = 'The telnet task does not support check mode'
        else:
            result['changed'] = True
            result['failed'] = False
 


            host = self._task.args.get('host', self._play_context.remote_addr)
            user = self._task.args.get('user', self._play_context.remote_user)
            password = self._task.args.get('password', self._play_context.password)

            # FIXME, default to play_context?
            port = self._task.args.get('port', '23')
            timeout = self._task.args.get('timeout', 520)
            pause = self._task.args.get('pause', 2)

            send_newline = self._task.args.get('send_newline', False)

            login_prompt = self._task.args.get('login_prompt', "login: ")
            password_prompt = self._task.args.get('password_prompt', "Password: ")
            prompts = self._task.args.get('prompts', ["\\$ "])
            commands = self._task.args.get('command') or self._task.args.get('commands')

            if isinstance(commands, text_type):
                commands = commands.split(',')

            if isinstance(commands, list) and commands:

                tn = telnetlib.Telnet(host, port, timeout)

                output = []
                in_cmd = []
                try:
                    if send_newline:
                        tn.write(b'\n')
                    tn.read_until(to_bytes(login_prompt))
                    tn.write(to_bytes(user + "\n"))

                    if password:
                        tn.read_until(to_bytes(password_prompt))
                        tn.write(to_bytes(password + "\n"))
                    tn.write(to_bytes("\x13"))## cntrl+s to go to the shell
                    tn.write("\n")#Enter
                    
                    for cmd in commands:
                        #display.vvvvv('>>> %s' % cmd)
                        tn.write(to_bytes(cmd + "\n"))
                        sleep(1)
                        #display.vvvvv('<<< %s' % cmd)
                        data = '' 
                        finish = '\n'
                        while data.find(finish) == -1:
                            data += tn.read_very_eager() # 
                                                    
                        #print (data)
                        temp = data.split(cmd,1)
                        res = temp[1].strip('\r\n')
                        res = res[:-14]
                        output.append(res)
                        in_cmd.append(cmd)
                                            
                        sleep(pause)
                    tn.write(b"exit\n")
                except EOFError as e:
                    result['failed'] = True
                    result['msg'] = 'Telnet action failed: %s' % to_native(e)
                finally:
                    if tn:
                        tn.close()
                    
            else:
                result['failed'] = True
        
        result['cli_result'] = output
        result['cli_input'] = in_cmd
        return result
