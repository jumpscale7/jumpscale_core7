
import re
import sys
from JumpScale import j
# from JumpScale.core.pmtypes import IPv4Address, IPv4Range
import textwrap
import string
import collections
import sys
import os
if sys.platform.startswith("win"):
    import msvcrt
    clear = lambda: os.system('cls')
else:
    clear = lambda: os.system('clear')


IPREGEX = "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

class Console:
    """
    class which groups functionality to print to a console
    self.width=120
    self.indent=0 #current indentation of messages send to console
    self.reformat=False #if True will make sure message fits nicely on screen
    """
    def __init__(self):
        self.width=230
        self.indent=0 #current indentation of messages send to console

    def rawInputPerChar(self,callback,params):
        """
        when typing, char per char will be returned
        """
        if not sys.platform.startswith("win"):
            j.system.platform.ubuntu.check()
            import termios
            fd = sys.stdin.fileno()

            oldterm = termios.tcgetattr(fd)
            newattr = termios.tcgetattr(fd)
            newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
            termios.tcsetattr(fd, termios.TCSANOW, newattr)

            cont=True
            try:
                while cont:
                    try:
                        c = sys.stdin.read(1)
                        cont, result, params = callback(c, params)
                    except IOError:
                        j.logger.exception("Failed to read one character from stdin", 5)
            finally:
                termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

        else:

            cont=True

            while cont:
                c = msvcrt.getch()
                cont, result, params = callback(c, params)

        return cont,result,params


    def _cleanline(self,line):
        """
        make sure is string
        """
        try:
            line=str(line)
        except:
            raise ValueError("Could not convert text to string in system class.")
        return line

    def formatMessage(self,message,prefix="",withStar=False,indent=0,width=0,removeemptylines=True):
        '''
        Reformat the message to display to the user and calculate length
        @param withStar means put * in front of message
        @returns: Length of last line and message to display
        @rtype: tuple<number, string>
        '''

        if indent==0 or indent==None:
            indent=self.indent

        #if j.transaction.hasRunningTransactions():
        #    maxLengthStatusType= 8 #nr chars
        #else:
        #    maxLengthStatusType=0

        if prefix!="":
            prefix="%s: "%(prefix)

        if withStar:
            prefix = '%s* %s' % (' ' * indent,prefix)
        else:
            prefix = ' %s%s' % (' ' * indent,prefix)

        if width==0:
            width=self.width
        maxMessageLength = width  -len(prefix) #- maxLengthStatusType
        if maxMessageLength<5:
            j.events.inputerror_critical("Cannot format message for screen, not enough width\nwidht:%s prefixwidth:%s maxlengthstatustype:%s" % (width,len(prefix),maxMessageLength),"console")

        out=[]
        for line in message.split("\n"):
            if removeemptylines and line=="":
                continue
            linelength=maxMessageLength
            linelength2=maxMessageLength-4
            prepend=""
            while len(line)>linelength:
                linenow="%s%s"%(prepend,line[:linelength])
                out.append(linenow)
                line=line[linelength:]
                linelength=linelength2 #room for prepend for next round
                prepend="    "
            linenow="%s%s"%(prepend,line[:linelength])
            out.append(linenow)

        return "\n".join(out)

    def echo(self, msg,indent=None,withStar=False,prefix="",log=False,lf=True):
        '''
        Display some text to the end-user, use this method instead of print
        @param indent std, will use indent from console object (same for all), this param allows to overrule
                will only work when j.console.reformat==True

        '''
        msg=str(msg)
        # if lf and msg!="" and msg[-1]!="\n":
        #     msg+="\n"
        msg=self._cleanline(msg)
        #if j.transaction.hasRunningTransactions() and withStar==False:
        #    indent=self.indent+1
        msg=self.formatMessage(msg,indent=indent,withStar=withStar,prefix=prefix).rstrip(" ")
        # msg=msg.rstrip()

        if "_stdout_ori" in sys.__dict__:
            sys._stdout_ori.write(msg)
        else:
            print(msg)
        j.logger.inlog=False
        if log:
            j.logger.log(msg,1)

    def info(self, text):
        print('\033[1;36m[*] %s\033[0m' % text)

    def warning(self, text):
        print('\033[1;33m[-] %s\033[0m' % text)

    def success(self, text):
        print('\033[1;32m[+] %s\033[0m' % text)

    def notice(self, text):
        print('\033[1;34m[+] %s\033[0m' % text)

    def message(self, text):
        print('\033[1;37m[+] %s\033[0m' % text)

    def echoListItem(self, msg):
        """
        Echo a list item
        @param msg: Message to display
        """
        self.echo(msg,withStar=True)

    def echoListItems(self, messages, sort=False):
        """
        Echo a sequence (iterator, generator, list, set) as list items

        @param messages: messages that need to be written to the console as list items
        @type messages: iterable
        @param sort: sort the messages before echoing them
        @type sort: bool
        @param loglevel: Log level
        @type loglevel: number
        """
        if sort:
            messages.sort()
        for msg in messages:
            self.echoListItem(msg)

    def echoWithPrefix(self,message,prefix,withStar=False,indent=None):
        """
        print a message which is formatted with a prefix
        """
        self.echo(message,prefix=prefix,withStar=withStar,indent=indent)

    def echoListWithPrefix(self,messages,prefix):
        """
        print messages
        """
        for message in messages:
            self.echoWithPrefix(message,prefix,withStar=True)

    def echoDict(self,dictionary,withStar=False,indent=None):
        for key in list(dictionary.keys()):
            try:
                self.echoWithPrefix(str(dictionary[key]),key,withStar,indent)
            except:
                j.events.inputerror_critical("Could not convert item of dictionary %s to string" % key,"console.echodict")

    def transformDictToMessage(self,dictionary,withStar=False,indent=None):
        for key in list(dictionary.keys()):
            try:
                self.formatMessage(str(dictionary[key]),key,withStar,indent)
            except:
                j.events.inputerror_critical("Could not convert item of dictionary %s to string" % key,"console.transformDictToMessage")

    def cls(self):
        """
        clear screen
        """
        clear()

    def askString(self, question, defaultparam='', regex=None, retry=-1, validate=None):
        """Get a string response on a question

        @param question: Question to respond to
        @param defaultparam: Default response on the question if response not passed
        @param regex: Regex to match in the response
        @param retry: Integer counter to retry ask for respone on the question
        @param validate: Function to validate provided value

        @returns: Response provided by the user
        @rtype: string
        """
        if j.application.interactive!=True:
            j.events.inputerror_critical ("Cannot ask a string in a non interactive mode.","console.askstring")
        if validate and not isinstance(validate, collections.Callable):
            raise TypeError('The validate argument should be a callable')
        response = ""
        if not defaultparam == "" and defaultparam:
            question += " [%s]"%defaultparam
        question += ": "
        retryCount = retry
        while retryCount != 0:
            if sys.version.startswith("2"):
                response = raw_input(question).rstrip()
            else:
                response = input(question).rstrip()
            if response == "" and not defaultparam == "" and defaultparam:
                return defaultparam
            if (not regex or re.match(regex,response)) and (not validate or validate(response)):
                return response
            else:
                self.echo( "Please insert a valid value!")
                retryCount = retryCount - 1
        raise ValueError("Console.askString() failed: tried %d times but user didn't fill out a value that matches '%s'." % (retry, regex))

    def askPassword(self, question, confirm=True, regex=None, retry=-1, validate=None):
        """Present a password input question to the user

        @param question: Password prompt message
        @param confirm: Ask to confirm the password
        @type confirm: bool
        @param regex: Regex to match in the response
        @param retry: Integer counter to retry ask for respone on the question
        @param validate: Function to validate provided value

        @returns: Password provided by the user
        @rtype: string
        """
        if j.application.interactive!=True:
            j.events.inputerror_critical ("Cannot ask a password in a non interactive mode.","console.askpasswd.noninteractive")
        if validate and not isinstance(validate, collections.Callable):
            raise TypeError('The validate argument should be a callable')
        response = ""
        import getpass
        startquestion = question
        if question.endswith(': '):
            question = question[:-2]
        question += ": "
        value=None
        failed = True
        retryCount = retry
        while retryCount != 0:
            response = getpass.getpass(question)
            if (not regex or re.match(regex,response)) and (not validate or validate(response)):
                if value == response or not confirm:
                    return response
                elif not value:
                    failed = False
                    value=response
                    question = "%s (confirm): " %(startquestion)
                else:
                    value=None
                    failed = True
                    question = "%s: "%(startquestion)
            if failed:
                self.echo("Invalid password!")
                retryCount = retryCount - 1
        j.events.inputerror_critical(("Console.askPassword() failed: tried %s times but user didn't fill out a value that matches '%s'." % (retry, regex)),"console.askpasswd")


    def askInteger(self, question, defaultValue = None, minValue = None, maxValue = None, retry = -1, validate=None):
        """Get an integer response on asked question

        @param question: Question need to get response on
        @param defaultparam: default response on the question if response not passed
        @param minValue: minimum accepted value for that integer
        @param maxValue: maximum accepted value for that integer
        @param retry: int counter to retry ask for respone on the question
        @param validate: Function to validate provided value

        @return: integer representing the response on the question
        """
        if j.application.interactive!=True:
            j.events.inputerror_critical ("Cannot ask an integer in a non interactive mode.")
        if validate and not isinstance(validate, collections.Callable):
            raise TypeError('The validate argument should be a callable')
        if not minValue == None and not maxValue == None:
            question += " (%d-%d)" % (minValue, maxValue)
        elif not minValue == None:
            question += " (min. %d)" % minValue
        elif not maxValue == None:
            question += " (max. %d)" % maxValue

        if not defaultValue == None:
            defaultValue=int(defaultValue)
            question += " [%d]" % defaultValue
        question += ": "

        retryCount = retry

        while retryCount != 0:
            if sys.version.startswith("2"):
                response = raw_input(question).rstrip(chr(13))
            else:
                response = input(question).rstrip(chr(13))
            if response == "" and not defaultValue == None:
                return defaultValue
            if (re.match("^-?[0-9]+$",response.strip())) and (not validate or validate(response)):
                responseInt = int(response.strip())
                if (minValue == None or responseInt >= minValue) and (maxValue == None or responseInt <= maxValue):
                    return responseInt
            j.console.echo("Please insert a valid value!")
            retryCount = retryCount - 1

        raise ValueError("Console.askInteger() failed: tried %d times but user didn't fill out a value that matches '%s'." % (retry, response))


    def askYesNo(self, message=""):
        '''Display a yes/no question and loop until a valid answer is entered

        @param message: Question message
        @type message: string

        @return: Positive or negative answer
        @rtype: bool
        '''
        if j.application.interactive!=True:
            j.events.inputerror_critical ("Cannot ask a yes/no question in a non interactive mode.","console.askyesno.notinteractive")

        while True:
            if sys.version.startswith("2"):
                result = raw_input(str(message) + " (y/n):").rstrip(chr(13))
            else:
                result = input(str(message) + " (y/n):").rstrip(chr(13))
            if result.lower() == 'y' or result.lower() == 'yes':
                return True
            if result.lower() == 'n' or result.lower() == 'no':
                return False
            self.echo( "Illegal value. Press 'y' or 'n'.")


    def askIntegers(self, question, invalid_message="invalid input please try again.", min=None, max=None):
        """
        Ask the user for multiple integers

        @param question: question that will be echoed before the user needs to input integers
        @type question: string
        @param invalid_message: message that will be echoed when the user inputs a faulty value
        @type invalid_message: string
        @param min: optional minimal value for input values, all returned values will be at least min
        @type min: number or None
        @param max: optional maximal value for input values, all returned values will be at least max
        @type max: number of None
        @return: the input numbers
        @rtype: list<number>
        """
        def clean(l):
            try:
                return [int(i.strip()) for i in l if i.strip() != ""]
            except ValueError as ex:
                return list()

        def all_between(l, min, max):
            for i in l:
                if (not min is None) and i < min:
                    return False
                elif (not max is None) and i > max:
                    return False
            return True

        def invalid(l):
            return len(l) == 0 or (not all_between(l, min, max))

        s = self.askString(question)
        if s.find("*")!=-1:
            return ["*"]
        s=s.split(",")

        parts = clean(s)
        while invalid(parts):
            self.echo(invalid_message)
            parts = clean(f())
        return parts

    def askChoice(self,choicearray, descr="", sort=True,maxchoice=25,height=30,autocomplete=False):
        """
        @param choicearray is list or dict, when dict key needs to be the object to return,
               the value of the dics is what needs to be returned, the key is the str representation
        """
        if height>0:
            self.cls()
        if isinstance(choicearray, (tuple, list)):
            choicearray.sort()

        #check items are strings or not, if not need to create dictionary
        if isinstance(choicearray, (tuple, list)):
            isstr=True
            for item in choicearray:
                if not j.basetype.string.check(item):
                    isstr=False
            if isstr==False:
                choicearrayNew={}
                for item in choicearray:
                    choicearrayNew[str(item)]=item
                choicearray=choicearrayNew

        def pprint4autocomplete(chars=""):
            self.cls()
            print
            counter=0
            if len(choicearray)>(height-3):

                if len(choicearray)<200:
                    shortchoice=[]
                    for item in choicearray:
                        short=item[0:4]
                        if short not in shortchoice:
                            shortchoice.append(short)
                        if len(shortchoice)>height-3:
                            break
                    shortchoice.sort()
                    for item in shortchoice:
                        print "- %s ..."%item
                        counter+=1

            else:
                for item in choicearray:
                    print "- %s"%item
                    counter+=1
            while counter<(height-3):
                print
                counter+=1
            descr2 = "%s\nMake a selection please, start typing, we will try to do auto completion.\n" % descr

            self.echo(descr2)
            print "        :%s"%chars,

        if len(choicearray)> maxchoice or autocomplete:
            wildcard=False
            chars=""

            while True:
                pprint4autocomplete(chars)

                params=[wildcard,chars]

                def process(char, params):
                    """
                    char per char will be returned from console
                    """
                    debug=False
                    wildcard, chars = params
                    #print (char,"","")
                    sys.stdout.write(char)
                    chars="%s%s" %(chars,char)
                    result=[]
                    if isinstance(choicearray, dict):
                        choicearray3=list(choicearray.values())
                    else:
                        choicearray3=choicearray

                    for rawChoice in choicearray3:
                        # We need to keep the 'raw' choices, so the end result is
                        # not a str()'d, lower()'d version of the original
                        # choicearray element.
                        choice=str(rawChoice).lower()

                        if wildcard and choice.find(chars.lower())!=-1:
                            result.append(rawChoice)

                        #print "%s %s %s %s" % (wildcard,choice,chars,choice.find(chars))
                        if not wildcard and choice.find(chars)==0:
                            # print "subset:%s"%rawChoice
                            result.append(rawChoice)
                        if char=="?":
                            return False,["99999"],params
                    params=[wildcard,chars]
                    #print str(len(result)) + " " + chars + " " + str(wildcard)
                    if not result:
                        # No matches
                        if debug:
                            print "nomatch"
                        params=[wildcard,chars[:-1]]
                        return False, result, params
                    elif len(result) < maxchoice:
                        #more than 1 result but not too many to show and ask choice with nr's
                        if debug:
                            print "<max amount, show items"

                        #try to find comonality beween remaining results
                        go=len(result)>0
                        x=1
                        chars2=chars
                        while go and len(result[0]) > x:
                            chars2+=result[0][x]
                            test=[item for item in result if item.find(chars2)==0]
                            if len(test)!=len(result):
                                #no match
                                chars2=chars2[:-1]
                                break
                            x+=1

                        params=[wildcard,chars2]

                        return False,result,params
                    else:
                        # Still too many results
                        if debug:
                            print "not small enough, keep typing"
                        return True, result, params

                cont,choicearray2,params = self.rawInputPerChar(process,params)
                wildcard, chars = params

                if len(choicearray2)==0:
                    wildcard=False
                    continue

                if len(choicearray2)==1 and not choicearray2==["99999"]:
                    #value was found
                    # wildcard, chars = params
                    # sys.stdout.write(str(choicearray2[0])[len(chars):])
                    return choicearray2[0]

                if choicearray2==["99999"]:
                    self.echo("\n")
                    for choice in choicearray:
                        choice=str(choice)
                        self.echoListItem(choice)
                    self.echo("\n")

                choicearray=choicearray2


            else:
                return self._askChoice(choicearray2, descr, sort)
        else:
            return self._askChoice(choicearray, descr, sort)


    def _askChoice(self, choicearray, descr=None, sort=True):
        if not choicearray:
            return None
        if len(choicearray) == 1:
            if isinstance(choicearray, list):
                self.echo("Found exactly one choice: %s"%(choicearray[0]))
                return choicearray[0]
            elif isinstance(choicearray, dict):
                item = choicearray.items()[0]
                self.echo("Found exactly one choice: %s"%(item[0]))
                return item[1]

        if j.application.interactive!=True:
            j.events.inputerror_critical ("Cannot ask a choice in an list of items in a non interactive mode.","console.askchoice.noninteractive")
        descr = descr or "\nMake a selection please: "

        if sort and isinstance(choicearray, (tuple, list)):
            choicearray.sort()

        self.echo(descr)
        if isinstance(choicearray, dict):
            keys=list(choicearray.keys())
            keys.sort()
            valuearray=[]
            choicearray2=[]
            for key in keys:
                valuearray.append(choicearray[key])
                choicearray2.append(key)
            choicearray=choicearray2

        elif isinstance(choicearray[0], (tuple, list)):
            valuearray = [ x[0] for x in choicearray ]
            choicearray = [ x[1] for x in choicearray ]
        else:
            valuearray = choicearray

        for idx, section in enumerate(choicearray):
            self.echo("   %s: %s" % (idx+1, section))
        self.echo("")
        result = self.askInteger("   Select Nr", minValue=1, maxValue=idx+1)

        return valuearray[result-1]

    def askChoiceMultiple(self, choicearray, descr=None, sort=True):
        if j.application.interactive!=True:
            j.events.inputerror_critical ("Cannot ask a choice in an list of items in a non interactive mode.","console.askChoiceMultiple.notinteractive")
        if not choicearray:
            return []
        if len(choicearray)==1:
            return choicearray

        descr = descr or "\nMake a selection please: "
        if sort:
            choicearray.sort()

        self.echo(descr)

        nr=0
        for section in choicearray:
            nr=nr+1
            self.echo("   %s: %s" % (nr, section))
        self.echo("")
        results = self.askIntegers("   Select Nr, use comma separation if more e.g. \"1,4\", * is all, 0 is None",
                                   "Invalid choice, please try again",
                                   min=0,
                                   max=len(choicearray))

        if results==["*"]:
            return choicearray
        elif results==[0]:
            return []
        else:
            return [choicearray[i-1] for i in results]

    def askMultiline(self, question, escapeString='.'):
        """
        Ask the user a question that needs a multi-line answer.

        @param question: The question that should be asked to the user
        @type question: string
        @param escapeString: Optional custom escape string that is used by the user to indicate input has ended.
        @type escapeString: string
        @return: string multi-line reply by the user, always ending with a newline
        """
        self.echo("%s:" % question)
        self.echo("(Enter answer over multiple lines, end by typing '%s' (without the quotes) on an empty line)" % escapeString)
        lines = []
        user_input=raw_input()
        while user_input != escapeString:
            lines.append(user_input)
            user_input=raw_input()
        lines.append("") # Forces end with newline
        return '\n'.join(lines)


    def showOutput(self):
        pass#@todo

    def hideOutput(self):
        pass

    def printOutput(self):
        pass

    def enableOutput(self):
	pass

    def showArray(self,array,header=True):
        choices=self._array2list(array,header)
        out=""
        for line in choices:
            out+="%s\n"%line
        print(out)
        return out

    def _array2list(self,array,header=True):
        def pad(s,length):
            while len(s)<length:
                s+=" "
            return s

        length={}
        for row in array:
            for x in range(len(row)):
                row[x]=str(row[x])
                if x not in length:
                    length[x]=0
                if length[x]<len(row[x]):
                    length[x]=len(row[x])

        choices=[]
        for row in array:
            line=""
            for x in range(len(row)):
                line+="| %s |"%pad(row[x],length[x])
            if line.strip()!="":
                line=line.replace("||","|")
                choices.append(line)
        choices.sort()
        return choices


    def askArrayRow(self,array,header=True,descr="",returncol=None):
        choices=self._array2list(array,header)
        result=self.askChoiceMultiple(choices,descr="")
        results=[]
        for item in result:
            if returncol==None:
                results.append([item.strip() for item in item.split("|") if item.strip()!=""])
            else:
                results.append(item.split("|")[returncol+1])

        if returncol!=None:
            return [item.strip(" ") for item in results]
        else:
            return results
