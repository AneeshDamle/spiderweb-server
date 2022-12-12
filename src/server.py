#import LIBRARY REFERENCES
import datetime #https://www.dataquest.io/blog/python-datetime-tutorial/
import socket   #https://docs.python.org/3/howto/sockets.html
from http import HTTPStatus
import http.client
import os       #https://www.geeksforgeeks.org/os-module-python-examples/

HOST = 'localhost'
PORT_NO = 8888


# print_type: prints values of variable along with type
# NOTE: Checking purpose
def print_type(var):
    print(var, type(var))

# TCPServer: Class for TCP server
# reference: https://bhch.github.io/posts/2017/11/writing-an-http-server-from-scratch/
class TCPServer:

    # initialise host and port number
    def __init__(self, host=HOST, port=PORT_NO):
        self.host = host
        self.port = port

    # get input action (HTTP request)
    def start(self):
        # connect server side via TCP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(50)
        print("Listening at", s.getsockname())

        # Keep getting client(browser) messages
        while True:
            conn, addr = s.accept()
            print("Connected by", addr)
            # read the request sent by the client
            request_data = conn.recv(1024)
            # generate a response according to the client request
            response = self.handle_request(request_data)
            # send back the data to client
            conn.sendall(response)
            # close the connection (demonstrates non-persistent connection)
            conn.close()

    # handle client-side requests 
    def handle_request(self, data):
        # will be overrided in subclass
        return data


# get_datetime: convert current date and time to HTTP request format
# FORMAT:   DAY, DD MMM YYYY HH:MM:SS IST
# Example:  Mon, 05 Dec 2022 19:00:37 IST
def get_datetime():
    today = datetime.datetime.today()
    datestr = today.strftime("%a, %d %b %Y %X IST")
    return datestr

# HTTPServer
class HTTPServer(TCPServer):
    headers = {
        'Server': 'AneeshChaServer',
        'Date': get_datetime(),
        'Content-Type': 'text/html',
    }

    # handle_request: handles client GET, PUT, POST, DELETE, HEAD requests
    def handle_request(self, request_data):
        # create an instance of `HTTPRequest`
        request = HTTPRequest(request_data)
        response = ''
        try:
            # Note: 
            # getattr: returns value of request.method attribute of self
            if (request.method == 'GET'):
                response = self.handle_GET(request)
            # HTML supports only GET, POST; hence DELETE will be built into POST
            if (request.method == 'POST'):
                response = self.handle_POST(request)
        except AttributeError:
            response = self.HTTP_501_handler(request)
 
        return response

    '''
    HTTP/1.1 200 OK            # The first line is called the response line
    Server: Tornado/4.3        # Response header
    Date: Wed, 18 Oct 2017     # Response header
    Content-type: text/html    # Response header
    Content-Length: 13         # Response header
                               # Blank line
    Hello, world!              # Response body
    '''
    # response_line: Returns response line with appropriate Status Code
    def response_line(self, status_code):
        reason = http.client.responses[status_code]
        line = "HTTP/1.1 %s%s\r\n" % (status_code, reason)

        return line.encode() # call encode to convert str to bytes

    def response_headers(self, extra_headers=None):
        headers_copy = self.headers.copy() # make a local copy of headers

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ""
        for h in headers_copy:
            headers += "%s: %s\r\n" % (h, headers_copy[h])
        return headers.encode()

    # Handles server-side issues with 50X requests
    def HTTP_501_handler(self, request):
        response_line = self.response_line(status_code=501)
        response_headers = self.response_headers()
        blank_line = b"\r\n"
        response_body = b"<h1>501 Not Implemented</h1>"
        return b"".join([response_line, response_headers, blank_line, response_body])

    # handle_GET: handles replies to client-side GET requests
    # Parse the GET request, extract information and build reply
    def handle_GET(self, request):
        filename = request.uri.strip('/') # remove the slash from the request URI
        # if a file is requested, check if it exists
        if os.path.exists(filename):
            response_line = self.response_line(status_code = HTTPStatus.OK.value)
            response_headers = self.response_headers()
            with open(filename, 'rb') as f:
                response_body = f.read()
        # Homepage
        elif filename == '':
            response_line = self.response_line(status_code = HTTPStatus.OK.value)
            response_headers = self.response_headers()
            with open('homepage.html', 'rb') as f:
                response_body = f.read()
        # if file DNE, respond with 404 NOT FOUND
        else:
            response_line = self.response_line(status_code = HTTPStatus.NOT_FOUND.value)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"

        blank_line = b"\r\n"

        return b"".join([response_line, response_headers, blank_line, response_body])

    # handle_POST: handles client-side POST requests
    # Application-oriented: Store TODO lists
    def handle_POST(self, request):
        flag = 0
        for line in request.header:
            if (flag == 1):
                print("Content mil gaya")
                inputs = line.split(b'&')
                todofile = inputs[0].split(b'=')[1]
                todotext = inputs[1].split(b'=')[1]
                print(todofile, todotext)
                # If DELETE option, pass the file to be deleted
                if (todotext == b'DELETE'):
                    print("Options for delete mate!")
                    return self.handle_DELETE(todofile)
                print("Content gaya")
                break
            if (line == b''):
                flag = 1

        if todofile:
            response_line = self.response_line(status_code = HTTPStatus.OK.value)
            response_headers = self.response_headers()
            with open(todofile, 'wb') as f:
                f.write(todotext)

            with open('homepage.html', 'rb') as f:
                response_body = f.read()
        # if file DNE, respond with 404 NOT FOUND
        else:
            response_line = self.response_line(status_code = HTTPStatus.NOT_FOUND.value)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"

        blank_line = b"\r\n"

        return b"".join([response_line, response_headers, blank_line, response_body])

    # Delete file and return
    def handle_DELETE(self, todofile):
        if os.path.exists(todofile):
            os.remove(todofile)
            response_line = self.response_line(status_code = HTTPStatus.OK.value)
            response_headers = self.response_headers()
            response_body = b"""<html>
                <body>
                <h1>File deleted!</h1>
                <body>
                </html>
            """

        else:
            print("The file does not exist")
            response_line = self.response_line(status_code = HTTPStatus.NOT_FOUND.value)
            response_headers = self.response_headers()
            response_body = b"<h1>404 Not Found</h1>"

        blank_line = b"\r\n"

        return b"".join([response_line, response_headers, blank_line, response_body])


'''
GET /index.html HTTP/1.1
Host: example.com
Connection: keep-alive
User-Agent: Mozilla/5.0
'''

'''
POST /test HTTP/1.1
Host: foo.example
Content-Type: application/x-www-form-urlencoded
Content-Length: 27

field1=value1&field2=value2
'''
class HTTPRequest:

    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = "1.1" # default to HTTP/1.1
        self.line = []
        self.header = []
        self.body = []
        # method to parse the request data
        self.parse(data)

    # Parses the HTTP request
    def parse(self, data):
        # Split the data in separate lines
        lines = data.split(b"\r\n")
        # First line is the request line
        request_line = lines[0]
        # Split the words in request line
        words = request_line.split(b" ")

        self.line = lines[0]
        for line in lines:
            if (line != self.line):
                self.header.append(line)

        self.method = words[0].decode() # convert bytes to str
        print(self.method)
        # TODO: Assess method
        if len(words) > 1:
            # we put this in an if-block because sometimes 
            # browsers don't send uri for homepage
            self.uri = words[1].decode() # convert bytes to str

        if len(words) > 2:
            self.http_version = words[2]



if __name__ == '__main__':
    server = HTTPServer()
    server.start()

