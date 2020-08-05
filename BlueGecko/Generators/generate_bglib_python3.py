# ================================================================
# Blue Gecko BLE API BGLib code generator: Python3 platform
# Jeff Rowberg <jeff@rowberg.net>
# Kris Young <kris.young@silabs.com>
# ----------------------------------------------------------------
#
# CHANGELOG:
#   2020-08-03 - Ported to Blue Gecko (Kris Young)
#   2017-06-26 - Moved to python3
#   2013-05-04 - Fixed single-item struct.unpack returns (@zwasson on Github)
#   2013-04-28 - Fixed numerous uint8array/bd_addr command arg errors
#              - Added 'debug' support
#   2013-04-16 - Fixed 'bglib_on_idle' to be 'on_idle'
#   2013-04-15 - Added wifi BGAPI support in addition to BLE BGAPI
#              - Fixed references to 'this' instead of 'self'
#   2013-04-11 - Initial release
#
# ================================================================
# Refer to LICENSE.md in the project repo for license details.

from xml.dom.minidom import parseString
import string
from datetime import datetime

# open, read, and close the BLEAPI XML data
print("Reading gecko.xml...")
file = open('gecko.xml', 'r')
data = file.read()
file.close()

# parse XML into a DOM structure
print("Parsing BLE API definition...")
dom = parseString(data)

# read relevant dom nodes for highlighter generation
ble_datatypes = dom.getElementsByTagName('datatype')
ble_classes = dom.getElementsByTagName('class')

#for ble_datatype in ble_datatypes:
#    print(ble_datatype.toxml())

ble_command_method_definitions = []
ble_response_callback_definitions = []
ble_response_callback_parser_conditions = []
ble_event_callback_definitions = []
ble_event_callback_parser_conditions = []
ble_constant_macros = []

for ble_class in ble_classes:
    class_name = ble_class.attributes['name'].value
    print("Gathering command, event, and enum data from main class '" + class_name + "'...")

    if len(ble_response_callback_parser_conditions) > 0:
        ble_response_callback_parser_conditions.append('elif packet_class == ' + ble_class.attributes['index'].value + ':')
    else:
        ble_response_callback_parser_conditions.append('if packet_class == ' + ble_class.attributes['index'].value + ':')

    num_responses = 0
    for ble_command in ble_class.getElementsByTagName('command'):
        #print(class_name + '_' + ble_command.attributes['name'].value)
        ble_command_name = class_name + '_' + ble_command.attributes['name'].value

        # gather parameter info, if present
        ble_params = ble_command.getElementsByTagName('params');
        parameters = ['self'] # python class methods require this
        payload_length = 0
        payload_additional = ''
        payload_parameters = []
        pack_pattern = '<4B'
        pack_args = ['0x20', '0', ble_class.attributes['index'].value, ble_command.attributes['index'].value]
        if len(ble_params) > 0:
            for ble_param in ble_params[0].getElementsByTagName('param'):
                parameters.append('' + ble_param.attributes['name'].value)
                if ble_param.attributes['type'].value == 'uint8':
                    pack_args.append('' + ble_param.attributes['name'].value)
                    pack_pattern += 'B'
                    payload_length += 1
                elif ble_param.attributes['type'].value == 'int8':
                    pack_args.append('' + ble_param.attributes['name'].value)
                    pack_pattern += 'b'
                    payload_length += 1
                elif ble_param.attributes['type'].value == 'uint16':
                    pack_args.append('' + ble_param.attributes['name'].value)
                    pack_pattern += 'H'
                    payload_length += 2
                elif ble_param.attributes['type'].value == 'int16':
                    pack_args.append('' + ble_param.attributes['name'].value)
                    pack_pattern += 'h'
                    payload_length += 2
                elif ble_param.attributes['type'].value == 'uint32':
                    pack_args.append('' + ble_param.attributes['name'].value)
                    pack_pattern += 'I'
                    payload_length += 4
                elif ble_param.attributes['type'].value == 'bd_addr':
                    pack_args.append('' + 'bytes(i for i in ' + ble_param.attributes['name'].value + ')')
                    pack_pattern += '6s'
                    payload_length += 6
                elif ble_param.attributes['type'].value == 'uint8array':
                    pack_args.append('len(' + ble_param.attributes['name'].value + ')')
                    pack_args.append('' + 'bytes(i for i in ' + ble_param.attributes['name'].value + ')')
                    pack_pattern += 'B\' + str(len(' + ble_param.attributes['name'].value + ')) + \'s'
                    payload_length += 1
                    payload_additional += ' + len(' + ble_param.attributes['name'].value + ')'

        pack_args[1] = str(payload_length)
        if len(payload_additional) > 0: pack_args[1] += payload_additional
        ble_command_method_definitions.append('def gecko_cmd_' + ble_command_name + '(' + ', '.join(parameters) + '):')
        ble_command_method_definitions.append('    return struct.pack(\'' + pack_pattern + '\', ' + ', '.join(pack_args) + ')')

        # gather return value info, if present
        ble_returns = ble_command.getElementsByTagName('returns');
        returns = []
        if len(ble_returns) > 0:
            for ble_return in ble_returns[0].getElementsByTagName('param'):
                returns.append(ble_return.attributes['type'].value + ' ' + ble_return.attributes['name'].value)

        ble_response_args = []
        obj_args = []
        unpack_pattern = '<'
        unpack_args = []
        payload_length = 0
        additional_code = []
        if len(ble_returns) > 0:
            for ble_return in ble_returns[0].getElementsByTagName('param'):
                if (ble_return.attributes['type'].value == 'uint8'):
                    unpack_pattern += 'B'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 1
                elif (ble_return.attributes['type'].value == 'uint16'):
                    unpack_pattern += 'H'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 2
                elif (ble_return.attributes['type'].value == 'uint32'):
                    unpack_pattern += 'I'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 4
                elif (ble_return.attributes['type'].value == 'int8'):
                    unpack_pattern += 'b'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 1
                elif (ble_return.attributes['type'].value == 'int16'):
                    unpack_pattern += 'h'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 2
                elif (ble_return.attributes['type'].value == 'int32'):
                    unpack_pattern += 'i'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 4
                elif (ble_return.attributes['type'].value == 'bd_addr'):
                    unpack_pattern += '6s'
                    unpack_args.append(ble_return.attributes['name'].value)
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value)
                    payload_length += 6
                    additional_code.append(ble_return.attributes['name'].value + ' = ' + ble_return.attributes['name'].value)
                elif (ble_return.attributes['type'].value == 'uint8array'):
                    unpack_pattern += 'B'
                    unpack_args.append(ble_return.attributes['name'].value + '_len')
                    obj_args.append("'" + ble_return.attributes['name'].value + "': " + ble_return.attributes['name'].value + '_data')
                    payload_length += 1
                    additional_code.append(ble_return.attributes['name'].value + '_data = self.bgapi_rx_payload[' + str(payload_length) + ':]')

        if num_responses > 0:
            ble_response_callback_parser_conditions.append('    elif packet_command == %s: # gecko_rsp_%s' % (ble_command.attributes['index'].value, ble_command_name))
        else:
            ble_response_callback_parser_conditions.append('    if packet_command == %s: # gecko_rsp_%s' % (ble_command.attributes['index'].value, ble_command_name))

        ble_response_code = []
        if payload_length > 0:
            if len(unpack_args) > 1:
                ble_response_code.append(', '.join(unpack_args) + ' = struct.unpack(\'' + unpack_pattern + '\', self.bgapi_rx_payload[:' + str(payload_length) + '])')
            else:
                # "struct.unpack" returns a tuple no matter what
                # (thanks @zwasson: https://github.com/jrowberg/bglib/issues/5)
                ble_response_code.append(', '.join(unpack_args) + ' = struct.unpack(\'' + unpack_pattern + '\', self.bgapi_rx_payload[:' + str(payload_length) + '])[0]')
        [ble_response_code.append(x) for x in additional_code]
        ble_response_code.append('self.gecko_rsp_' + ble_command_name + '({ ' + ', '.join(obj_args) + ' })')
        ble_response_callback_parser_conditions.append('        ' + '\n                        '.join(ble_response_code))
        if ble_class.attributes['index'].value == '0' and ble_command.attributes['index'].value == '0':
            ble_response_callback_parser_conditions.append('        self.busy = False')
            ble_response_callback_parser_conditions.append('        self.on_idle()')

        ble_response_callback_definitions.append('gecko_rsp_' + ble_command_name + ' = BGAPIEvent()')
        num_responses += 1

    if num_responses == 0:
        ble_response_callback_parser_conditions.pop()

    if len(ble_event_callback_parser_conditions) > 0:
        ble_event_callback_parser_conditions.append('elif packet_class == ' + ble_class.attributes['index'].value + ':')
    else:
        ble_event_callback_parser_conditions.append('if packet_class == ' + ble_class.attributes['index'].value + ':')

    num_events = 0
    for ble_event in ble_class.getElementsByTagName('event'):
        #print(class_name + '_' + ble_event.attributes['name'].value)
        ble_event_name = class_name + '_' + ble_event.attributes['name'].value

        # gather parameter info, if present
        ble_params = ble_event.getElementsByTagName('params');
        obj_args = []
        unpack_pattern = '<'
        unpack_args = []
        payload_length = 0
        additional_code = []
        if len(ble_params) > 0:
            for ble_param in ble_params[0].getElementsByTagName('param'):
                if (ble_param.attributes['type'].value == 'uint8'):
                    unpack_pattern += 'B'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 1
                elif (ble_param.attributes['type'].value == 'uint16'):
                    unpack_pattern += 'H'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 2
                elif (ble_param.attributes['type'].value == 'uint32'):
                    unpack_pattern += 'I'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 4
                elif (ble_param.attributes['type'].value == 'int8'):
                    unpack_pattern += 'b'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 1
                elif (ble_param.attributes['type'].value == 'int16'):
                    unpack_pattern += 'h'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 2
                elif (ble_param.attributes['type'].value == 'int32'):
                    unpack_pattern += 'i'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 4
                elif (ble_param.attributes['type'].value == 'bd_addr'):
                    unpack_pattern += '6s'
                    unpack_args.append(ble_param.attributes['name'].value)
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value)
                    payload_length += 6
                    additional_code.append(ble_param.attributes['name'].value + ' = ' + ble_param.attributes['name'].value)
                elif (ble_param.attributes['type'].value == 'uint8array'):
                    unpack_pattern += 'B'
                    unpack_args.append(ble_param.attributes['name'].value + '_len')
                    obj_args.append("'" + ble_param.attributes['name'].value + "': " + ble_param.attributes['name'].value + '_data')
                    payload_length += 1
                    additional_code.append(ble_param.attributes['name'].value + '_data = self.bgapi_rx_payload[' + str(payload_length) + ':]')

        if num_events > 0:
            ble_event_callback_parser_conditions.append('    elif packet_command == %s: # gecko_evt_%s' % (ble_event.attributes['index'].value, ble_event_name))
        else:
            ble_event_callback_parser_conditions.append('    if packet_command == %s: # gecko_evt_%s' % (ble_event.attributes['index'].value, ble_event_name))

        ble_event_code = []
        if payload_length > 0:
            if len(unpack_args) > 1:
                ble_event_code.append(', '.join(unpack_args) + ' = struct.unpack(\'' + unpack_pattern + '\', self.bgapi_rx_payload[:' + str(payload_length) + '])')
            else:
                # "struct.unpack" returns a tuple no matter what
                # (thanks @zwasson: https://github.com/jrowberg/bglib/issues/5)
                ble_event_code.append(', '.join(unpack_args) + ' = struct.unpack(\'' + unpack_pattern + '\', self.bgapi_rx_payload[:' + str(payload_length) + '])[0]')
        [ble_event_code.append(x) for x in additional_code]
        ble_event_code.append('self.gecko_evt_' + ble_event_name + '({ ' + ', '.join(obj_args) + ' })')
        ble_event_callback_parser_conditions.append('        ' + '\n                        '.join(ble_event_code))
        if ble_class.attributes['index'].value == '0' and ble_event.attributes['index'].value == '0':
            ble_event_callback_parser_conditions.append('        self.busy = False')
            ble_event_callback_parser_conditions.append('        self.on_idle()')

        ble_event_callback_definitions.append('gecko_evt_' + ble_event_name + ' = BGAPIEvent()')
        num_events += 1

    if num_events == 0:
        ble_event_callback_parser_conditions.pop()

    for ble_enum in ble_class.getElementsByTagName('enum'):
        #print(class_name + '_' + ble_enum.attributes['name'].value)
        enum_name = class_name + '_' + ble_enum.attributes['name'].value
        ble_constant_macros.append('#define BGLIB_' + (enum_name.upper() + ' ').ljust(54) + ble_enum.attributes['value'].value)

    if len(ble_constant_macros) > 0 and ble_constant_macros[len(ble_constant_macros) - 1] != '':
        ble_constant_macros.append('')

# create Python library file(s)
print("Writing Python source library files...")
source = open('bglib.py', 'w')
source.write('#!/usr/bin/env python\n\
\n\
""" Blue Gecko BGAPI/BGLib implementation\n\
\n\
Changelog:\n\
    2020-08-03 - Ported to Blue Gecko v2.x API (Kris Young)\n\
    2017-06-26 - Moved to python3\n\
    2013-05-04 - Fixed single-item struct.unpack returns (@zwasson on Github)\n\
    2013-04-28 - Fixed numerous uint8array/bd_addr command arg errors\n\
               - Added \'debug\' support\n\
    2013-04-16 - Fixed \'bglib_on_idle\' to be \'on_idle\'\n\
    2013-04-15 - Added wifi BGAPI support in addition to BLE BGAPI\n\
               - Fixed references to \'this\' instead of \'self\'\n\
    2013-04-11 - Initial release\n\
\n\
============================================\n\
Blue Gecko BGLib Python interface library\n\
2013-05-04 by Jeff Rowberg <jeff@rowberg.net>\n\
Updates should (hopefully) always be available at https://github.com/jrowberg/bglib\n\
\n\
============================================\n\
BGLib Python interface library code is placed under the MIT license\n\
Copyright (c) 2013 Jeff Rowberg\n\
Copyright (c) 2020 Silicon Laboratories\n\
Permission is hereby granted, free of charge, to any person obtaining a copy\n\
of this software and associated documentation files (the "Software"), to deal\n\
in the Software without restriction, including without limitation the rights\n\
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n\
copies of the Software, and to permit persons to whom the Software is\n\
furnished to do so, subject to the following conditions:\n\
\n\
The above copyright notice and this permission notice shall be included in\n\
all copies or substantial portions of the Software.\n\
\n\
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n\
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n\
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n\
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n\
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n\
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN\n\
THE SOFTWARE.\n\
===============================================\n'
+ 'Generated on {}'.format(datetime.now().strftime("%Y-%b-%d %H:%M:%S")) +
'\n===============================================\n\
\n\
"""\n\
\n\
__author__ = "Jeff Rowberg"\n\
__license__ = "MIT"\n\
__version__ = "2013-05-04"\n\
__email__ = "jeff@rowberg.net"\n\
\n\
import struct\n\
\n\
\n\
# thanks to Masaaki Shibata for Python event handler code\n\
# http://www.emptypage.jp/notes/pyevent.en.html\n\
\n\
class BGAPIEvent(object):\n\
\n\
    def __init__(self, doc=None):\n\
        self.__doc__ = doc\n\
\n\
    def __get__(self, obj, objtype=None):\n\
        if obj is None:\n\
            return self\n\
        return BGAPIEventHandler(self, obj)\n\
\n\
    def __set__(self, obj, value):\n\
        pass\n\
\n\
\n\
class BGAPIEventHandler(object):\n\
\n\
    def __init__(self, event, obj):\n\
\n\
        self.event = event\n\
        self.obj = obj\n\
\n\
    def _getfunctionlist(self):\n\
\n\
        """(internal use) """\n\
\n\
        try:\n\
            eventhandler = self.obj.__eventhandler__\n\
        except AttributeError:\n\
            eventhandler = self.obj.__eventhandler__ = {}\n\
        return eventhandler.setdefault(self.event, [])\n\
\n\
    def add(self, func):\n\
\n\
        """Add new event handler function.\n\
\n\
        Event handler function must be defined like func(sender, earg).\n\
        You can add handler also by using \'+=\' operator.\n\
        """\n\
\n\
        self._getfunctionlist().append(func)\n\
        return self\n\
\n\
    def remove(self, func):\n\
\n\
        """Remove existing event handler function.\n\
\n\
        You can remove handler also by using \'-=\' operator.\n\
        """\n\
\n\
        self._getfunctionlist().remove(func)\n\
        return self\n\
\n\
    def fire(self, earg=None):\n\
\n\
        """Fire event and call all handler functions\n\
\n\
        You can call EventHandler object itself like e(earg) instead of\n\
        e.fire(earg).\n\
        """\n\
\n\
        for func in self._getfunctionlist():\n\
            func(self.obj, earg)\n\
\n\
    __iadd__ = add\n\
    __isub__ = remove\n\
    __call__ = fire\n\
\n\
\n\
class BGLib(object):\n\
\n\
    ' + ('\n    '.join(ble_command_method_definitions)) + '\n\n\
    ' + ('\n    '.join(ble_response_callback_definitions)) + '\n\n\
    ' + ('\n    '.join(ble_event_callback_definitions)) + '\n\
\n\
    on_busy = BGAPIEvent()\n\
    on_idle = BGAPIEvent()\n\
    on_timeout = BGAPIEvent()\n\
    on_before_tx_command = BGAPIEvent()\n\
    on_tx_command_complete = BGAPIEvent()\n\
\n\
    bgapi_rx_buffer = b""\n\
    bgapi_rx_expected_length = 0\n\
    busy = False\n\
    debug = False\n\
\n\
    def send_command(self, ser, packet):\n\
        if self.debug: print(\'=>[ \' + \' \'.join([\'%02X\' % b for b in packet]) + \' ]\')\n\
        self.on_before_tx_command()\n\
        self.busy = True\n\
        self.on_busy()\n\
        ser.write(packet)\n\
        self.on_tx_command_complete()\n\
\n\
    def check_activity(self, ser, timeout=0):\n\
        if timeout > 0:\n\
            ser.timeout = timeout\n\
            while 1:\n\
                x = ser.read()\n\
                if len(x) > 0:\n\
                    self.parse(x)\n\
                else: # timeout\n\
                    self.busy = False\n\
                    self.on_idle()\n\
                    self.on_timeout()\n\
                if not self.busy: # finished\n\
                    break\n\
        else:\n\
            while ser.inWaiting(): self.parse(ser.read())\n\
        return self.busy\n\
\n\
    def parse(self, barray):\n\
        b=barray[0]\n\
        if len(self.bgapi_rx_buffer) == 0 and (b == 0xa0 or b == 0x20):\n\
            self.bgapi_rx_buffer+=bytes([b])\n\
        elif len(self.bgapi_rx_buffer) == 1:\n\
            self.bgapi_rx_buffer+=bytes([b])\n\
            self.bgapi_rx_expected_length = 4 + (self.bgapi_rx_buffer[0] & 0x07) + self.bgapi_rx_buffer[1]\n\
        elif len(self.bgapi_rx_buffer) > 1:\n\
            self.bgapi_rx_buffer+=bytes([b])\n\
\n\
        """\n\
        BGAPI packet structure (as of 2020-06-12):\n\
            Byte 0:\n\
                  [7] - 1 bit, Message Type (MT)         0 = Command/Response, 1 = Event\n\
                [6:3] - 4 bits, Technology Type (TT)     0010 - Blue Gecko\n\
                [2:0] - 3 bits, Length High (LH)         Payload length (high bits)\n\
            Byte 1:     8 bits, Length Low (LL)          Payload length (low bits)\n\
            Byte 2:     8 bits, Class ID (CID)           Command class ID\n\
            Byte 3:     8 bits, Command ID (CMD)         Command ID\n\
            Bytes 4-n:  0 - 2048 Bytes, Payload (PL)     Up to 2048 bytes of payload\n\
        """\n\
\n\
        #print\'%02X: %d, %d\' % (b, len(self.bgapi_rx_buffer), self.bgapi_rx_expected_length)\n\
        if self.bgapi_rx_expected_length > 0 and len(self.bgapi_rx_buffer) == self.bgapi_rx_expected_length:\n\
            if self.debug: print(\'<=[ \' + \' \'.join([\'%02X\' % b for b in self.bgapi_rx_buffer ]) + \' ]\')\n\
            packet_type, payload_length, packet_class, packet_command = self.bgapi_rx_buffer[:4]\n\
            self.bgapi_rx_payload = self.bgapi_rx_buffer[4:]\n\
            self.bgapi_rx_buffer = b""\n\
            if packet_type & 0xa0 == 0x20:\n\
                # 0x20 = Blue Gecko response packet\n\
                ' + ('\n                '.join(ble_response_callback_parser_conditions)) + '\n\
                self.busy = False\n\
                self.on_idle()\n\
            elif packet_type & 0xa0 == 0xa0:\n\
                # 0xa0 = Blue Gecko event packet\n\
                ' + ('\n                '.join(ble_event_callback_parser_conditions)) + '\n\
\n\
# ================================================================\n\
\n\
')
source.close()

print("Finished!\n")

print("Python Installation Instructions:")
print("====================================")
print("1. Add bglib.py to your project")
print("2. Import bglib.* in your source file(s)")
print("3. Add event handlers for desired BGLib response and event packets\n")
