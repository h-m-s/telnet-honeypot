import logging
from logging import config
import sys
from structlog import configure, processors, stdlib, threadlocal

def setup_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'format': '%(asctime)s %(message)s %(lineno)d %(pathname)s',
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
		'stream': sys.stdout,
                'formatter': 'json',
                'level': logging.DEBUG,
            },
            'json': {
                'class': 'logging.FileHandler',
		'filename': '/var/log/hms/telnet.log',
                'formatter': 'json',
                'level': logging.INFO,
            }
        },
        'loggers': {
            'telnet': {
                'handlers': ['json', 'console'],
                'level': logging.DEBUG
            }
        }
    })
    
    configure(
        context_class=threadlocal.wrap_dict(dict),
        logger_factory=stdlib.LoggerFactory(),
        wrapper_class=stdlib.BoundLogger,
        processors=[
            stdlib.filter_by_level,
            stdlib.add_logger_name,
            stdlib.add_log_level,
            stdlib.PositionalArgumentsFormatter(),
            processors.TimeStamper(fmt="iso"),
            processors.StackInfoRenderer(),
            processors.format_exc_info,
            processors.UnicodeDecoder(),
            processors.KeyValueRenderer()
        ]
    )

    """
    Drops the requests loggers to WARNING level.
    Super, duper spammy otherwise, because it'll try to show you
    every GET/POST made to the docker socket.
    """
    logging.getLogger("requests").setLevel(logging.WARNING)    
