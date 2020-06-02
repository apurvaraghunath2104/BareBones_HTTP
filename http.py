import socket
import sys
import ssl


def transfer_encoding(data):
    chunked_data = b""
    while True:
        data1 = data.split(b"\r\n", 1)
        chunk_sperator = data1[0]
        if chunk_sperator == b'0':
            break
        chunk_sperator_int = int(chunk_sperator, 16)
        chunk = data1[1]
        chunked_data = chunked_data + chunk[:chunk_sperator_int]
        data = chunk[chunk_sperator_int + 2:]
    return chunked_data


def retrieve_url(url):
    """
        return bytes of the body of the document at url
    """
    # return b"this is unlikely to be correct"
    if "http://" in url:
        url = url.replace("http://", '')

    elif "https://" in url:
        url = url.replace("https://", '')
        pos = url.split("/", 1)
        host = pos[0]
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
        ssl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            ssl_socket.connect((host, 443))
            s = ssl_context.wrap_socket(ssl_socket)
        except socket.error:
            return None
        path = "/" + pos[1]
        https_request = ("GET " + path + " HTTP/1.1\r\nHost: " + host + "\r\nConnection: close\r\n\r\n")
        s.send(https_request.encode())
        data = s.recv(4096)
        full_data = data
        while True:
            data = s.recv(4096)
            if not data:
                break
            full_data += data
        if b'200 OK' in full_data:
            if b'Transfer-Encoding: chunked\r\n' not in full_data:
                final_data_pos = full_data.split(b"\r\n\r\n", 1)
                final_data = final_data_pos[1]
                return final_data
            elif b'Transfer-Encoding: chunked' in full_data:
                final_data_pos = full_data.split(b"\r\n\r\n", 1)
                final_data = final_data_pos[1]
                data = transfer_encoding(final_data)
                return data
        else:
            return None

    url_count = url.count("/")
    if url_count != 0:
        path_pos = url.split('/', 1)
        path = "/" + path_pos[1]
        if "/" in url:
            host_pos = url.find("/")
            host = url[0:host_pos]
    elif url_count == 0:
        path = "/"
        host = url

    if ':' in host:
        colon_pos = host.split(":")
        port = int(colon_pos[1])
        host = colon_pos[0]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((bytes(host, 'utf-8'), port))
        except socket.error:
            return None
        http_request = 'GET {} HTTP/1.1\r\nHost: {}:{}\r\nConnection: close\r\n\r\n'
        http_request = http_request.format(path, host, port)
        s.send(http_request.encode())
    else:
        port = 80
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((bytes(host, 'utf-8'), port))
        except socket.error:
            return None
        http_request = ('GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n' % (path, host))
        s.send(bytes(http_request, 'utf-8'))

    data = s.recv(4096)
    while data != b'':
        full_data = data
        while True:
            data = s.recv(4096)
            if not data:
                break
            full_data += data
        if b'200 OK' in full_data:
            if b'Transfer-Encoding: chunked\r\n' not in full_data:
                final_data_pos = full_data.split(b"\r\n\r\n", 1)
                final_data = final_data_pos[1]
                return final_data
            elif b'Transfer-Encoding: chunked' in full_data:
                final_data_pos = full_data.split(b"\r\n\r\n", 1)
                final_data = final_data_pos[1]
                data = transfer_encoding(final_data)
                return data
            else:
                return None
        else:
            if b'Location: ' in full_data:
                pos_url = full_data.find(b'Location: ')
                url1 = full_data[pos_url:]
                url2 = url1.replace(b'Location: ', b'')
                pos_url2 = url2.find(b'\r\n')
                url3 = url2[:pos_url2]
                new_url = url3.decode('utf-8')
                retrieve_url(new_url)
            else:
                return None


if __name__ == "__main__":
    sys.stdout.buffer.write(retrieve_url(sys.argv[1]))