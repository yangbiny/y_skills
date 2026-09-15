"""Bounded MySQL queries. stdout belongs exclusively to the MCP transport."""
from __future__ import annotations

import configparser
import datetime as dt
import decimal
import json
import logging
import math
import os
import socket
import ssl
import stat
import threading
import time
from contextlib import suppress
from pathlib import Path

import anyio
import pymysql
import sqlglot
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from sqlglot import exp

CONFIG = Path('/Users/knowreason/y_skills/.mysql_conf')
MAX_ROWS = 500
# Leave room for the MCP envelope; tools return text once, not duplicated JSON.
RESULT_BYTES = 1024 * 1024 - 16384
SYSTEM_DATABASES = {'mysql', 'sys', 'information_schema', 'performance_schema'}
SLOTS = threading.BoundedSemaphore(2)

# Fail closed when the parser introduces a new expression or function type.
NODES = frozenset('''Select Union Subquery With CTE From Table TableAlias Column
Identifier Literal Null Boolean Star Alias Distinct Join Where Group Having Order
Ordered Limit Offset Paren And Or Not EQ NEQ GT GTE LT LTE Is In Between Like ILike
Escape Add Sub Mul Div IntDiv Mod Neg Case If DataType DataTypeParam Interval Var
Tuple'''.split())
FUNCTIONS = frozenset('''Case Count Sum Avg Min Max Abs Round Floor Ceil Coalesce Nullif
If Concat ConcatWs Lower Upper Length Trim Substring Replace Cast Date DateAdd
DateSub DateDiff CurrentDate CurrentTimestamp Year Month Day Extract TimeToStr
StrToDate'''.split())
UNITS = frozenset('YEAR QUARTER MONTH WEEK DAY HOUR MINUTE SECOND MICROSECOND'.split())


class Rejected(Exception):
    """A fixed, credential-free message safe to expose to the model."""


def read_config() -> dict:
    try:
        fd = os.open(CONFIG, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 65536):
                raise Rejected('CONFIG_PERMISSIONS: 配置须属于当前用户、权限为 600，且为普通小文件。')
            parser = configparser.ConfigParser(interpolation=None)
            parser.read_file(stream)
        if set(parser.sections()) != {'mysql', 'tls'} or parser.defaults():
            raise ValueError('sections')
        mysql = parser['mysql']
        if set(mysql) - {'host', 'port', 'user', 'password', 'database'}:
            raise ValueError('unknown key')
        options = {key: mysql[key] for key in ('host', 'user', 'password', 'database')}
        if any(not value.strip() for value in options.values()):
            raise ValueError('empty field')
        options['port'] = mysql.getint('port', 3306)
        if not 1 <= options['port'] <= 65535:
            raise ValueError('port')
        if options['database'].lower() in SYSTEM_DATABASES:
            raise ValueError('system database')
        tls = parser['tls']
        if set(tls) - {'enabled', 'ca_file'}:
            raise ValueError('unknown TLS key')
        enabled = tls.getboolean('enabled', True)
        ca = tls.get('ca_file', '').strip()
        if ca and not Path(ca).is_absolute():
            raise ValueError('CA must be absolute')
        options['ssl'] = ssl.create_default_context(cafile=ca or None) if enabled else None
        options['ssl_disabled'] = not enabled
        options['password'] = options['password'].encode('utf-8')
        return options
    except Rejected:
        raise
    except Exception:
        raise Rejected('CONFIG_INVALID: 配置缺失、不完整或无效，请由用户检查 .mysql_conf；不要读取或回显凭据。') from None


def prepare_query(sql: str, database: str) -> tuple[str, int]:
    if not isinstance(sql, str) or not sql.strip() or len(sql.encode('utf-8')) > 65536:
        raise Rejected('SQL_INVALID: 查询为空或超过 64 KiB。')
    try:
        statements = sqlglot.parse(sql, read='mysql', error_level=sqlglot.ErrorLevel.RAISE)
        if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.Union)):
            raise Rejected('SQL_REJECTED: 仅允许单条 SELECT 或 UNION 查询。')
        tree = statements[0]
        for node in tree.walk():
            kind = type(node).__name__
            if node.comments:
                raise Rejected('SQL_REJECTED: 不允许注释或 SQL 提示。')
            # SQLGlot models AND/OR and CASE as Func too; check both explicit
            # allowlists so ordinary predicates are not mistaken for unknown calls.
            if kind not in NODES and kind not in FUNCTIONS:
                if isinstance(node, exp.Func):
                    raise Rejected('SQL_REJECTED: 使用了未批准的函数。')
                raise Rejected('SQL_REJECTED: 包含不支持或不安全的 SQL 结构。')
            if isinstance(node, exp.Select):
                allowed = {'expressions', 'from_', 'joins', 'where', 'group', 'having',
                           'order', 'limit', 'offset', 'with_', 'distinct'}
                if any(value and key not in allowed for key, value in node.args.items()):
                    raise Rejected('SQL_REJECTED: 不允许 SELECT 修饰、锁定或输出选项。')
            if isinstance(node, exp.With) and node.args.get('recursive'):
                raise Rejected('SQL_REJECTED: 不允许递归 CTE。')
            if isinstance(node, (exp.Table, exp.Column)):
                if node.catalog or (node.db and node.db != database):
                    raise Rejected('SQL_REJECTED: 不允许跨库访问。')
                if isinstance(node, exp.Table):
                    if not isinstance(node.this, exp.Identifier):
                        raise Rejected('SQL_REJECTED: 不允许动态表或表函数。')
                    if any(v and k not in {'this', 'db', 'catalog', 'alias'} for k, v in node.args.items()):
                        raise Rejected('SQL_REJECTED: 不允许表提示或表修饰。')
            if isinstance(node, exp.Star):
                if not isinstance(node.parent, exp.Count) or node.parent.this is not node:
                    raise Rejected('SQL_REJECTED: 请明确选择字段，只有 COUNT(*) 可以使用星号。')
            if isinstance(node, exp.Var) and node.name.upper() not in UNITS:
                raise Rejected('SQL_REJECTED: 不支持该 SQL 单位或变量。')
            if isinstance(node, (exp.Limit, exp.Offset)):
                value = node.expression
                if not isinstance(value, exp.Literal) or value.is_string or not value.this.isdigit():
                    raise Rejected('SQL_REJECTED: LIMIT 和 OFFSET 必须是非负整数字面量。')
        limit = tree.args.get('limit')
        requested = int(limit.expression.this) if limit else None
        cap = min(requested, MAX_ROWS) if requested is not None else 100
        # Preserve an explicit small LIMIT. Fetch one extra only when we impose a cap.
        fetch = cap if requested is not None and requested <= MAX_ROWS else cap + 1
        tree = tree.limit(fetch, copy=False)
        return tree.sql(dialect='mysql', unsupported_level=sqlglot.ErrorLevel.RAISE), cap
    except Rejected:
        raise
    except Exception:
        raise Rejected('SQL_INVALID: 无法安全解析或生成该 MySQL 查询。') from None


def encode_value(value):
    if isinstance(value, (bytes, bytearray, memoryview)):
        return '[binary omitted]'
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, dt.timedelta):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def packed(value) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def read_rows(cursor, cap: int) -> tuple[dict, bool]:
    columns = [{'name': item[0], 'type_code': item[1]} for item in cursor.description or ()]
    result = {'columns': columns, 'rows': [], 'row_count': 0, 'truncated': False}
    size = len(packed(result))
    if size > RESULT_BYTES // 2:
        raise Rejected('RESULT_TOO_WIDE: 列信息超过返回大小限制。')
    exhausted = False
    while True:
        row = cursor.fetchone()
        if row is None:
            exhausted = True
            break
        values = [encode_value(value) for value in row]
        added = len(packed(values)) + 1
        if len(result['rows']) >= cap or size + added > RESULT_BYTES // 2:
            result['truncated'] = True
            break
        result['rows'].append(values)
        size += added
    result['row_count'] = len(result['rows'])
    return result, exhausted


def execute_tool(operation: str, argument: str | None = None) -> str:
    if not SLOTS.acquire(blocking=False):
        return packed({'error': 'BUSY', 'message': '当前已有两个查询，请稍后重试。'})
    start = time.monotonic()
    connection = None
    cursor = None
    timer = None
    expired = threading.Event()
    fully_read = False
    try:
        options = read_config()
        database = options['database']
        if operation == 'query':
            statement, cap = prepare_query(argument, database)
        elif operation == 'describe':
            if not argument or len(argument) > 64 or '\x00' in argument:
                raise Rejected('TABLE_INVALID: 请提供单个有效表名。')
            statement, cap = '', MAX_ROWS
        else:
            statement, cap = 'SHOW FULL TABLES', MAX_ROWS
        connection = pymysql.connect(
            **options, charset='utf8mb4', connect_timeout=5, read_timeout=7,
            write_timeout=5, autocommit=False, local_infile=False,
            cursorclass=pymysql.cursors.SSCursor,
            sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION',
        )
        # Defense in depth: verify the negotiated transport as well as requiring TLS.
        if options['ssl'] is not None and not isinstance(connection._sock, ssl.SSLSocket):
            raise Rejected('TLS_REQUIRED: 数据库未建立经过验证的 TLS 连接。')

        def interrupt_socket():
            expired.set()
            # Shutdown interrupts blocking reads without running a second SQL command.
            with suppress(OSError, AttributeError):
                connection._sock.shutdown(socket.SHUT_RDWR)

        timer = threading.Timer(8, interrupt_socket)
        timer.daemon = True
        timer.start()
        cursor = connection.cursor()
        cursor.execute('SET SESSION max_execution_time = 5000')
        cursor.execute('START TRANSACTION READ ONLY')
        if operation == 'describe':
            name = '`' + argument.replace('`', '``') + '`'
            cursor.execute('SHOW COLUMNS FROM ' + name)
            columns, fully_read = read_rows(cursor, MAX_ROWS)
            if not fully_read:
                raise Rejected('METADATA_TOO_LARGE: 字段元数据过大。')
            fully_read = False
            cursor.execute('SHOW INDEX FROM ' + name)
            indexes, fully_read = read_rows(cursor, MAX_ROWS)
            result = {'table': argument, 'columns': columns, 'indexes': indexes,
                      'truncated': columns['truncated'] or indexes['truncated']}
        else:
            cursor.execute(statement)
            result, fully_read = read_rows(cursor, cap)
        if expired.is_set():
            raise Rejected('QUERY_TIMEOUT: 查询已超过时间限制。')
        result['elapsed_ms'] = round((time.monotonic() - start) * 1000)
        # Check escaped text size too, since this JSON is embedded in MCP JSON.
        payload = packed(result)
        if len(packed(payload)) > RESULT_BYTES:
            raise Rejected('RESULT_TOO_LARGE: 编码后的结果超过 1 MiB 限制，请缩小查询。')
        return payload
    except Rejected as error:
        return packed({'error': str(error).split(':', 1)[0], 'message': str(error)})
    except pymysql.MySQLError as error:
        code = error.args[0] if error.args and isinstance(error.args[0], int) else None
        return packed({'error': 'QUERY_TIMEOUT' if expired.is_set() or code == 3024 else 'DATABASE_ERROR',
                       'code': code, 'message': '数据库操作失败；请检查授权、网络、配置或查询，服务不回显原始错误。'})
    except Exception:
        return packed({'error': 'INTERNAL_ERROR', 'message': '操作未完成，原始异常已隐藏以保护凭据和数据。'})
    finally:
        if connection is not None:
            # Never close an unfinished SSCursor: close() drains the remaining result.
            # Disconnecting aborts the transaction when streaming was interrupted.
            if fully_read and not expired.is_set():
                with suppress(Exception):
                    connection.rollback()
            with suppress(Exception):
                connection.close()
            # The driver's cursor/result destructors otherwise try to drain the
            # disconnected stream, producing unraisable exceptions and cycles.
            for result in (connection._result, getattr(cursor, '_result', None)):
                if result is not None:
                    result.unbuffered_active = False
                    result.connection = None
            if cursor is not None:
                cursor.connection = None
        if timer is not None:
            timer.cancel()
            timer.join()
        SLOTS.release()


mcp = FastMCP('mysql-readonly', log_level='CRITICAL')


@mcp.tool(
    structured_output=False,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
)
async def list_tables() -> str:
    """列出配置数据库中账号可访问的表和视图；最多 500 条。"""
    return await anyio.to_thread.run_sync(execute_tool, 'list')


@mcp.tool(
    structured_output=False,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
)
async def describe_table(table: str) -> str:
    """查看当前库内单个表或视图的字段及索引，不接受数据库名参数。"""
    return await anyio.to_thread.run_sync(execute_tool, 'describe', table)


@mcp.tool(
    structured_output=False,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
)
async def query_readonly(sql: str) -> str:
    """执行当前库内受限 SELECT；默认 100 行、最多 500 行、SQL 执行限制 5 秒。"""
    return await anyio.to_thread.run_sync(execute_tool, 'query', sql)


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    mcp.run(transport='stdio')
