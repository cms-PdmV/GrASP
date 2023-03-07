"""
Main module that starts flask web server
"""
import os
import os.path
import logging
import logging.handlers
import argparse
from app import app, set_app


def main():
    """
    Main function: start Flask web server
    """
    parser = argparse.ArgumentParser(description="GrASP Webpage")
    parser.add_argument("--port", help="Port, default is 8002", type=int, default=8002)
    parser.add_argument(
        "--host", help="Host IP, default is 127.0.0.1", default="127.0.0.1"
    )
    parser.add_argument("--debug", help="Run Flask in debug mode", action="store_true")
    parser.add_argument("--db_auth", help="Path to GrASP database auth file")
    args = vars(parser.parse_args())
    port = args.get("port")
    host = args.get("host")
    debug = args.get("debug")
    db_auth = args.get("db_auth")

    logger = logging.getLogger()

    # Set Flask app configuration
    set_app(db_auth=db_auth, debug=debug)

    # Write PID to a file
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # Do only once, before the reloader
        pid = os.getpid()
        logger.info("PID: %s", pid)
        with open("grasp.pid", "w", encoding="utf-8") as pid_file:
            pid_file.write(str(pid))

    logger.info("Starting GrASP, host=%s, port=%s, debug=%s", host, port, debug)
    # Run flask
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
