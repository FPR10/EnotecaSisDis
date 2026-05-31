import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """
    Configura il logger root dell'applicazione.
    In produzione: livello INFO, formato compatto.
    In debug: livello DEBUG, formato esteso con nome file e riga.
    """
    level = logging.DEBUG if debug else logging.INFO

    fmt_debug = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    fmt_prod = "%(asctime)s | %(levelname)-8s | %(message)s"

    logging.basicConfig(
        level=level,
        format=fmt_debug if debug else fmt_prod,
        
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silenzia i logger verbosi di librerie terze
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if debug else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Shortcut per ottenere un logger nominato per modulo."""
    return logging.getLogger(name)
