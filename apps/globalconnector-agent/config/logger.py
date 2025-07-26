import sys

from loguru import logger


def custom_std_formatter(record):
    record["message"] = (
        record["message"]
        .replace("\n", " ")
        .replace("{", "{{")
        .replace("}", "}}")
        + "\n"
    )
    if record["extra"].get("file", None):
        record["extra"]["file"] = record["extra"]["file"].rsplit("/")[-1]
        return (
            "<level>{level: <8}</level> - "
            "<green>{extra[file]: >24}:{extra[line]: <4}</green> - "
            "<level>{message}</level>".format(**record)
        )
    return (
        "<level>{level: <8}</level> - "
        "<green>{file: >24}:{line: <4}</green> - "
        "<level>{message}</level>".format(**record)
    )


def custom_log_formatter(record):
    record["message"] = (
        record["message"]
        .replace("\n", " ")
        .replace("{", "{{")
        .replace("}", "}}")
        + "\n"
    )
    if record["extra"].get("file", None):
        record["extra"]["file"] = record["extra"]["file"].rsplit("/")[-1]
        return (
            "{extra[request_id]} - {time} - "
            "{level: <8} - {extra[file]: >24}:{extra[line]: <4} - "
            "{message}".format(**record)
        )

    if not record["extra"].get("request_id", None):
        record["extra"]["request_id"] = "INITIALIZATION"

    return (
        "{extra[request_id]:<36} - {time} - "
        "{level: <8} - {file: >24}:{line: <4} - "
        "{message}".format(**record)
    )


def get_logger():
    logger.remove()
    logger.add(
        sys.stdout, format=custom_std_formatter, colorize=True, level="INFO"
    )
    logger.add(
        "logs/log.log",
        rotation="00:00",
        retention=7,
        format=custom_log_formatter,
        level="DEBUG",
    )

    return logger
