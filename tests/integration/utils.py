from psutil import net_connections


def count_open_connections(host="127.0.0.1", port=8080):
    """Count ESTABLISHED connections to specific host:port"""
    count = 0
    for conn in net_connections(kind="tcp"):
        if (
            conn.status == "ESTABLISHED"
            and conn.raddr
            and conn.raddr[:2] == (host, port)
        ):
            count += 1
    return count
