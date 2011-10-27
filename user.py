#    This file is part of GrooveBot.
#
#    GrooveBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GrooveBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GrooveBot.  If not, see <http://www.gnu.org/licenses/>.


from shove import Shove

class UserHandler:
    def __init__(self):
        self.__db = Shove('sqlite:///users.db')
        for table in ['karma', 'group', 'command']:
            if not self.__db.get(table):
                self.__db[table] = dict()
        self.__db['group']['Qalthos'] = 'op'

    def get_karma(self, user):
        return self.__db['karma'].get(user, 0)

    def set_perms(self, user, group):
        self.__db['group'][user] = group

    def get_perms(self, user):
        return self.__db['group'].get(user)

    def set_group(self, command, group):
        self.__db['command'][command] = group

    def get_group(self, command):
        return self.__db['command'].get(command)

    def has_perms(self, user, command):
        return not self.get_group(command) or self.get_perms(user) == self.get_group(command)
